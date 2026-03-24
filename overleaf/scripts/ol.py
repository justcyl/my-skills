#!/usr/bin/env python3
"""
Overleaf CLI 包装器。

通过环境变量认证（而非从浏览器读取 Cookie），支持以下操作：
  ls [PATH]                  列出项目或文件
  read <PROJECT/PATH>        读取文件内容到标准输出
  write <PROJECT/PATH>       从标准输入写入文件
  edit <PROJECT/PATH>        按 old/new 精确匹配进行增量编辑
  review list <PROJECT>      获取项目 review 评论线程
  review locate <PROJECT> <THREAD_ID>
                             自动定位该 review 可能对应的文件
  review resolve <PROJECT> <THREAD_ID>
                             标记指定 review 线程为已解决
  mkdir [-p] <PROJECT/PATH>  创建目录
  rm <PROJECT/PATH>          删除文件或目录
  download <PROJECT> <OUT>   下载项目为 ZIP

环境变量：
  OVERLEAF_HOST    Overleaf 实例域名（不含协议），如 overleaf.mycompany.com
  OVERLEAF_COOKIE  浏览器 Cookie 字符串，如 "overleaf_session2=xxx; gke-route=yyy"
"""

import os
import sys
import shutil
import json
import io as pyio
import pathlib
import zipfile
from typing import Any
import click

# 确保在找不到 pyoverleaf 时给出清晰的错误信息
try:
    from pyoverleaf import Api, ProjectIO
except ImportError:
    print(
        "错误：无法导入 pyoverleaf。请确认使用正确的 Python 解释器运行本脚本：\n"
        "  ~/.local/share/uv/tools/pyoverleaf/bin/python overleaf/scripts/ol.py <cmd>",
        file=sys.stderr,
    )
    sys.exit(1)


def _build_api() -> Api:
    """从环境变量构建已认证的 API 实例。"""
    host = os.environ.get("OVERLEAF_HOST", "www.overleaf.com")
    # 去除可能附带的 https:// 前缀
    host = host.removeprefix("https://").removeprefix("http://").rstrip("/")

    cookie_str = os.environ.get("OVERLEAF_COOKIE", "").strip()
    if not cookie_str:
        raise click.ClickException(
            "环境变量 OVERLEAF_COOKIE 未设置。\n"
            "请将浏览器中的 Overleaf Cookie 头部字符串写入该变量，例如：\n"
            "  export OVERLEAF_COOKIE='overleaf_session2=s%3Axxx; gke-route=yyy'"
        )

    # 解析 "name=value; name2=value2" 格式的 Cookie 字符串
    cookies: dict[str, str] = {}
    for segment in cookie_str.split(";"):
        segment = segment.strip()
        if "=" in segment:
            name, _, value = segment.partition("=")
            cookies[name.strip()] = value.strip()
        elif segment:
            cookies[segment] = ""

    api = Api(host=host)
    api.login_from_cookies(cookies)
    return api


def _resolve_project(api: Api, project_name_or_id: str) -> tuple[str, str]:
    """将项目名或项目 ID 解析为 (project_id, project_name)。"""
    projects = api.get_projects()
    for project in projects:
        if project.name == project_name_or_id or project.id == project_name_or_id:
            return project.id, project.name

    names = ", ".join(p.name for p in projects)
    raise click.ClickException(
        f"项目 '{project_name_or_id}' 不存在。当前可用项目：{names}"
    )


def _resolve_project_and_path_to_ids(api: Api, path: str) -> tuple[str, str, str]:
    """
    将 <项目名>/<相对路径> 解析为 (project_id, project_name, rel_path)。
    """
    if path.startswith("/"):
        path = path[1:]
    if "/" not in path:
        raise click.BadParameter(
            f"路径 '{path}' 格式错误，应为 <项目名>/<文件路径>，例如：MyProject/main.tex"
        )
    project_name, _, rel_path = path.partition("/")
    project_id, resolved_project_name = _resolve_project(api, project_name)
    if not rel_path:
        raise click.BadParameter("文件路径不能为空。")
    return project_id, resolved_project_name, rel_path


def _resolve_project_and_path(api: Api, path: str):
    """
    将 <项目名>/<相对路径> 解析为 (ProjectIO, rel_path)。

    路径格式：MyProject/chapters/intro.tex
    """
    if path.startswith("/"):
        path = path[1:]
    if "/" not in path:
        raise click.BadParameter(
            f"路径 '{path}' 格式错误，应为 <项目名>/<文件路径>，例如：MyProject/main.tex"
        )
    project_name, _, rel_path = path.partition("/")
    project_id, _ = _resolve_project(api, project_name)
    return ProjectIO(api, project_id), rel_path


def _review_get(
    api: Api, project_id: str, suffix: str, *, expected_json: bool = True
) -> Any:
    """调用 review GET 接口，兼容不同部署路径。"""
    candidates = [
        f"https://{api._host}/project/{project_id}/{suffix}",  # pylint: disable=protected-access
        f"https://{api._host}/chat/project/{project_id}/{suffix}",  # pylint: disable=protected-access
    ]
    session = api._get_session()  # pylint: disable=protected-access
    request_kwargs = dict(api._request_kwargs)  # pylint: disable=protected-access
    request_kwargs["headers"] = {"Accept": "application/json"}

    errors: list[str] = []
    for url in candidates:
        resp = session.get(url, **request_kwargs)
        if resp.status_code in {401, 403}:
            raise click.ClickException(
                "认证失败（401/403）。请检查 OVERLEAF_COOKIE 是否过期。"
            )
        if resp.status_code == 404:
            errors.append(f"{url} -> 404")
            continue
        try:
            resp.raise_for_status()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            errors.append(f"{url} -> {exc}")
            continue

        if not expected_json:
            return resp
        try:
            return resp.json()
        except ValueError:
            errors.append(f"{url} -> 非 JSON 响应（可能被重定向到登录页）")
            continue

    raise click.ClickException(
        "接口调用失败。尝试过以下路径但均失败：\n- " + "\n- ".join(errors)
    )


def _review_post(api: Api, project_id: str, suffix: str, payload: dict[str, Any]) -> None:
    """调用 review POST 接口，兼容不同部署路径。"""
    candidates = [
        f"https://{api._host}/project/{project_id}/{suffix}",  # pylint: disable=protected-access
        f"https://{api._host}/chat/project/{project_id}/{suffix}",  # pylint: disable=protected-access
    ]
    session = api._get_session()  # pylint: disable=protected-access
    request_kwargs = dict(api._request_kwargs)  # pylint: disable=protected-access
    csrf = api._get_csrf_token(project_id)  # pylint: disable=protected-access
    headers = {
        "Referer": f"https://{api._host}/project/{project_id}",  # pylint: disable=protected-access
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "x-csrf-token": csrf,
    }
    request_kwargs["headers"] = headers

    errors: list[str] = []
    for url in candidates:
        resp = session.post(url, json=payload, **request_kwargs)
        if resp.status_code in {401, 403}:
            raise click.ClickException(
                "认证失败（401/403）。请检查 OVERLEAF_COOKIE 是否过期。"
            )
        if resp.status_code == 404:
            errors.append(f"{url} -> 404")
            continue
        try:
            resp.raise_for_status()
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            errors.append(f"{url} -> {exc}")
            continue

    raise click.ClickException(
        "接口调用失败。尝试过以下路径但均失败：\n- " + "\n- ".join(errors)
    )


def _fetch_review_threads(api: Api, project_id: str) -> dict[str, Any]:
    """获取项目的评论线程（review threads）。"""
    data = _review_get(api, project_id, "threads")
    if not isinstance(data, dict):
        raise click.ClickException("review 接口返回结构异常（期望 object）。")
    return data


def _read_file_from_project_zip(api: Api, project_id: str, rel_path: str) -> str:
    """从项目 ZIP 中读取文本文件内容，避免 doc 读取链路导致乱码。"""
    zip_bytes = api.download_project(project_id)
    normalized = pathlib.PurePosixPath(rel_path).as_posix().lstrip("/")
    with zipfile.ZipFile(pyio.BytesIO(zip_bytes), "r") as zf:
        names = zf.namelist()
        candidate_map = {name.lstrip("/"): name for name in names}
        name = candidate_map.get(normalized)
        if name is None:
            # 兼容部分 zip 中包含前缀目录的情况
            matched = [n for n in names if n.lstrip("/").endswith("/" + normalized)]
            if len(matched) == 1:
                name = matched[0]
            else:
                raise click.ClickException(f"在项目 ZIP 中找不到文件：{rel_path}")
        raw = zf.read(name)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise click.ClickException(
            f"文件 '{rel_path}' 不是 UTF-8 文本，无法执行 edit：{exc}"
        ) from exc


def _collect_project_docs(api: Api, project_id: str) -> list[dict[str, str]]:
    """收集项目中的所有 doc（带路径）。"""
    root = api.project_get_files(project_id)
    stack: list[tuple[str, Any]] = [("", root)]
    docs: list[dict[str, str]] = []
    while stack:
        prefix, folder = stack.pop()
        for child in folder.children:
            child_type = getattr(child, "type", None)
            if child_type == "folder":
                stack.append((f"{prefix}{child.name}/", child))
            elif child_type == "doc":
                docs.append({"doc_id": child.id, "path": f"{prefix}{child.name}"})
    docs.sort(key=lambda item: item["path"])
    return docs


def _pull_doc_join_payload(api: Api, project_id: str, doc_id: str) -> list[Any]:
    """拉取单个 doc 的 joinDoc payload。"""
    socket = None
    try:
        socket = api._open_socket(project_id)  # pylint: disable=protected-access
        while True:
            line = socket.recv()
            if line.startswith("7:"):
                raise RuntimeError("Could not open doc socket.")
            if line.startswith("5:"):
                break

        socket.send('5:1+::{"name":"clientTracking.getConnectedUsers"}'.encode("utf-8"))
        socket.send(
            f'5:2+::{{"name": "joinDoc", "args": ["{doc_id}", {{"encodeRanges": true}}]}}'.encode("utf-8")
        )

        payload = None
        while True:
            line = socket.recv()
            if line.startswith("7:"):
                raise RuntimeError("Could not join doc.")
            if line.startswith("6:::2+"):
                payload = line[6:]
                break
        assert payload is not None
        data = json.loads(payload)
        if not isinstance(data, list):
            raise RuntimeError("Unexpected joinDoc payload type.")
        return data
    finally:
        if socket is not None:
            try:
                socket.send(f'5:3+::{{"name": "leaveDoc", "args": ["{doc_id}"]}}'.encode("utf-8"))
                while True:
                    line = socket.recv()
                    if line.startswith("6:::3+"):
                        break
                    if line.startswith("7:"):
                        break
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            socket.close()


def _position_to_line(lines: list[str], position: Any) -> int | None:
    """将文档字符位移转换为大致行号（1-based）。"""
    if not isinstance(position, int) or position < 0:
        return None
    offset = 0
    for idx, line in enumerate(lines, start=1):
        line_len = len(line)
        if position <= offset + line_len:
            return idx
        offset += line_len + 1
    return len(lines) if lines else 1


def _build_thread_doc_locations(api: Api, project_id: str) -> dict[str, list[dict[str, Any]]]:
    """
    基于 doc comments 原生数据构建 thread -> doc/path 映射。
    """
    docs = _collect_project_docs(api, project_id)
    mapping: dict[str, list[dict[str, Any]]] = {}

    for doc in docs:
        payload = _pull_doc_join_payload(api, project_id, doc["doc_id"])
        lines_raw = payload[1] if len(payload) > 1 and isinstance(payload[1], list) else []
        lines = [str(x) for x in lines_raw]
        meta = payload[4] if len(payload) > 4 and isinstance(payload[4], dict) else {}
        comments = meta.get("comments", [])
        if not isinstance(comments, list):
            continue

        for comment in comments:
            if not isinstance(comment, dict):
                continue
            op = comment.get("op")
            op_dict = op if isinstance(op, dict) else {}
            thread_id = comment.get("id") or op_dict.get("t")
            if not isinstance(thread_id, str) or not thread_id:
                continue

            position = op_dict.get("p")
            ref = {
                "doc_id": doc["doc_id"],
                "path": doc["path"],
                "position": position if isinstance(position, int) else None,
                "line": _position_to_line(lines, position),
                "op": op_dict,
                "metadata": comment.get("metadata"),
            }
            mapping.setdefault(thread_id, []).append(ref)

    return mapping


def _print_review_summary(project_name: str, threads: dict[str, Any]) -> None:
    """打印 review 统计信息。"""
    total = len(threads)
    resolved = sum(
        1 for item in threads.values() if isinstance(item, dict) and item.get("resolved")
    )
    open_threads = total - resolved
    print(
        f"项目 '{project_name}' review 统计：总计 {total}，未解决 {open_threads}，已解决 {resolved}",
        file=sys.stderr,
    )


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Overleaf CLI — 使用 OVERLEAF_COOKIE / OVERLEAF_HOST 环境变量认证。"""


@cli.command("ls")
@click.argument("path", default=".")
def cmd_ls(path: str):
    """列出所有项目（无参数），或列出项目内的文件。

    示例：
      ol.py ls                       # 列出全部项目
      ol.py ls MyProject             # 列出项目根目录
      ol.py ls MyProject/chapters    # 列出子目录
    """
    api = _build_api()
    if not path or path in {".", "/"}:
        for p in api.get_projects():
            print(p.name)
    else:
        io, rel_path = _resolve_project_and_path(api, path if "/" in path else path + "/")
        # 对项目根目录做特殊处理（rel_path 为空字符串）
        files = io.listdir(rel_path)
        print("\n".join(files))


@cli.command("read")
@click.argument("path")
def cmd_read(path: str):
    """读取项目文件并输出到标准输出。

    示例：
      ol.py read MyProject/main.tex
    """
    api = _build_api()
    io, rel_path = _resolve_project_and_path(api, path)
    with io.open(rel_path, "rb") as f:
        shutil.copyfileobj(f, sys.stdout.buffer)


@cli.command("write")
@click.argument("path")
def cmd_write(path: str):
    """从标准输入读取内容并写入项目文件（覆盖）。

    示例：
      echo 'Hello' | ol.py write MyProject/hello.tex
      cat local.tex | ol.py write MyProject/main.tex
    """
    api = _build_api()
    io, rel_path = _resolve_project_and_path(api, path)
    with io.open(rel_path, "wb+") as f:
        shutil.copyfileobj(sys.stdin.buffer, f)
    print(f"已写入：{path}", file=sys.stderr)


@cli.command("edit")
@click.argument("path")
@click.option("--old", "old_text", required=True, help="需要匹配并替换的原始文本。")
@click.option("--new", "new_text", required=True, help="替换后的新文本。")
@click.option(
    "--replace-all",
    is_flag=True,
    help="替换所有匹配；默认要求 old 仅匹配 1 处。",
)
def cmd_edit(path: str, old_text: str, new_text: str, replace_all: bool):
    """按精确文本匹配进行编辑（类似 codex/opencode 的 edit 语义）。"""
    if old_text == "":
        raise click.BadParameter("--old 不能为空字符串。")

    api = _build_api()
    project_id, project_name, rel_path = _resolve_project_and_path_to_ids(api, path)
    original = _read_file_from_project_zip(api, project_id, rel_path)

    matches = original.count(old_text)
    if matches == 0:
        raise click.ClickException("edit 失败：old_text 未匹配到任何内容（0 处）。")
    if not replace_all and matches > 1:
        raise click.ClickException(
            f"edit 失败：old_text 匹配到 {matches} 处。"
            "默认要求唯一匹配；如需全部替换请加 --replace-all。"
        )

    replaced = matches if replace_all else 1
    updated = (
        original.replace(old_text, new_text)
        if replace_all
        else original.replace(old_text, new_text, 1)
    )
    io = ProjectIO(api, project_id)
    with io.open(rel_path, "w", encoding="utf-8") as f:
        f.write(updated)
    print(
        f"已编辑：{project_name}/{rel_path}（替换 {replaced} 处）",
        file=sys.stderr,
    )


@cli.command("mkdir")
@click.option("-p", "--parents", is_flag=True, help="自动创建缺失的中间目录。")
@click.argument("path")
def cmd_mkdir(path: str, parents: bool):
    """在项目中创建目录。

    示例：
      ol.py mkdir MyProject/figures
      ol.py mkdir -p MyProject/a/b/c
    """
    api = _build_api()
    io, rel_path = _resolve_project_and_path(api, path)
    io.mkdir(rel_path, parents=parents, exist_ok=parents)
    print(f"目录已创建：{rel_path}", file=sys.stderr)


@cli.command("rm")
@click.argument("path")
def cmd_rm(path: str):
    """删除项目中的文件或目录。

    示例：
      ol.py rm MyProject/old_draft.tex
    """
    api = _build_api()
    io, rel_path = _resolve_project_and_path(api, path)
    io.remove(rel_path)
    print(f"已删除：{rel_path}", file=sys.stderr)


@cli.command("download")
@click.argument("project")
@click.argument("output_path")
def cmd_download(project: str, output_path: str):
    """将整个项目下载为 ZIP 文件。

    示例：
      ol.py download MyProject /tmp/MyProject.zip
    """
    api = _build_api()
    project_id, project_name = _resolve_project(api, project)
    api.download_project(project_id, output_path)
    print(f"项目 '{project_name}' 已下载到：{output_path}")


@cli.group("review")
def cmd_review():
    """Review 相关命令。"""


@cmd_review.command("list")
@click.argument("project")
@click.option("--compact", is_flag=True, help="使用紧凑 JSON 输出（默认为带缩进）。")
def cmd_review_list(project: str, compact: bool):
    """获取项目 review 评论线程数据并输出为 JSON。"""
    api = _build_api()
    project_id, project_name = _resolve_project(api, project)
    threads = _fetch_review_threads(api, project_id)
    _print_review_summary(project_name, threads)
    locations = _build_thread_doc_locations(api, project_id)

    reviews: list[dict[str, Any]] = []
    for thread_id, thread_raw in threads.items():
        if not isinstance(thread_raw, dict):
            continue
        refs = locations.get(thread_id, [])
        reviews.append(
            {
                "thread_id": thread_id,
                "resolved": bool(thread_raw.get("resolved")),
                "resolved_at": thread_raw.get("resolved_at"),
                "resolved_by_user_id": thread_raw.get("resolved_by_user_id"),
                "resolved_by_user": thread_raw.get("resolved_by_user"),
                "messages": thread_raw.get("messages", []),
                "location": {
                    "count": len(refs),
                    "primary": refs[0] if refs else None,
                    "all": refs,
                },
            }
        )
    reviews.sort(key=lambda item: (item["resolved"], item["thread_id"]))

    print(
        json.dumps(
            {
                "project": {"id": project_id, "name": project_name},
                "review_count": len(reviews),
                "reviews": reviews,
            },
            ensure_ascii=False,
            indent=None if compact else 2,
        )
    )


@cmd_review.command("locate")
@click.argument("project")
@click.argument("thread_id")
@click.option("--compact", is_flag=True, help="使用紧凑 JSON 输出（默认为带缩进）。")
def cmd_review_locate(project: str, thread_id: str, compact: bool):
    """精确定位单条 review 对应的 doc/path。"""
    api = _build_api()
    project_id, project_name = _resolve_project(api, project)
    threads = _fetch_review_threads(api, project_id)
    thread = threads.get(thread_id)
    if not isinstance(thread, dict):
        raise click.ClickException(f"线程 {thread_id} 不存在。")

    locations = _build_thread_doc_locations(api, project_id)
    refs = locations.get(thread_id, [])
    print(
        json.dumps(
            {
                "project": {"id": project_id, "name": project_name},
                "thread_id": thread_id,
                "location": {
                    "count": len(refs),
                    "primary": refs[0] if refs else None,
                    "all": refs,
                },
            },
            ensure_ascii=False,
            indent=None if compact else 2,
        )
    )


@cmd_review.command("resolve")
@click.argument("project")
@click.argument("thread_id")
@click.option("--user-id", help="可选。指定 resolve 的 user_id。默认取该线程首条消息 user_id。")
def cmd_review_resolve(project: str, thread_id: str, user_id: str | None):
    """将指定 review 线程标记为已解决。"""
    api = _build_api()
    project_id, project_name = _resolve_project(api, project)

    resolved_user_id = user_id
    threads = _fetch_review_threads(api, project_id)
    if resolved_user_id is None:
        thread = threads.get(thread_id)
        if isinstance(thread, dict):
            messages = thread.get("messages")
            if isinstance(messages, list) and messages:
                first = messages[0]
                if isinstance(first, dict):
                    maybe = first.get("user_id")
                    if isinstance(maybe, str) and maybe:
                        resolved_user_id = maybe

    payload: dict[str, Any] = {}
    if resolved_user_id:
        payload["user_id"] = resolved_user_id

    locations = _build_thread_doc_locations(api, project_id)
    refs = locations.get(thread_id, [])
    if not refs:
        raise click.ClickException(
            f"无法定位线程 {thread_id} 对应的 doc，不能执行 resolve。"
        )

    unique_doc_ids: list[str] = []
    for ref in refs:
        doc_id = ref.get("doc_id")
        if isinstance(doc_id, str) and doc_id not in unique_doc_ids:
            unique_doc_ids.append(doc_id)

    resolve_errors: list[str] = []
    resolved = False
    for doc_id in unique_doc_ids:
        try:
            _review_post(
                api,
                project_id,
                f"doc/{doc_id}/thread/{thread_id}/resolve",
                payload,
            )
            resolved = True
            break
        except click.ClickException as doc_exc:
            resolve_errors.append(str(doc_exc))

    if not resolved:
        raise click.ClickException(
            "review resolve 失败。尝试 doc 级接口后仍失败。\n\n" + "\n\n".join(resolve_errors)
        )

    # 二次确认
    new_threads = _fetch_review_threads(api, project_id)
    new_thread = new_threads.get(thread_id)
    is_resolved = isinstance(new_thread, dict) and bool(new_thread.get("resolved"))
    if not is_resolved:
        raise click.ClickException(
            f"线程 {thread_id} 请求已发送，但复查仍未标记 resolved。请在网页端确认权限或状态。"
        )
    print(f"项目 '{project_name}' 线程 {thread_id} 已标记为 resolved。")


if __name__ == "__main__":
    cli()
