#!/usr/bin/env python3
"""
Overleaf CLI 包装器（精简版：git + review + compile + pdf）。

支持以下操作：
  git urls                   获取每个项目的 Git 地址
  create <NAME>              创建新 Overleaf 项目
  review list <PROJECT>      获取项目 review 评论线程（含位置信息）
  review resolve <PROJECT> <THREAD_ID>
                             标记指定 review 线程为已解决
  compile <PROJECT>          触发 PDF 编译，输出编译结果 JSON
  pdf <PROJECT>              编译并下载 PDF 到本地

环境变量：
  OVERLEAF_HOST    Overleaf 实例域名（不含协议），如 overleaf.mycompany.com
  OVERLEAF_COOKIE  浏览器 Cookie 字符串，如 "overleaf_session2=xxx; gke-route=yyy"
"""

import os
import sys
import json
import pathlib
from urllib.parse import urlparse, urlunparse
from typing import Any
import click

try:
    from pyoverleaf import Api
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
    host = host.removeprefix("https://").removeprefix("http://").rstrip("/")

    cookie_str = os.environ.get("OVERLEAF_COOKIE", "").strip()
    if not cookie_str:
        raise click.ClickException(
            "环境变量 OVERLEAF_COOKIE 未设置。\n"
            "请将浏览器中的 Overleaf Cookie 头部字符串写入该变量，例如：\n"
            "  export OVERLEAF_COOKIE='overleaf_session2=s%3Axxx; gke-route=yyy'"
        )

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


def _fetch_user_projects_json(api: Api) -> dict[str, Any]:
    """通过 /user/projects 接口获取项目列表 JSON。"""
    url = f"https://{api._host}/user/projects"
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
    headers = dict(request_kwargs.get("headers", {}))
    headers["Accept"] = "application/json"
    request_kwargs["headers"] = headers

    resp = session.get(url, **request_kwargs)
    if resp.status_code in {401, 403}:
        raise click.ClickException(
            "认证失败（401/403）。请检查 OVERLEAF_COOKIE 是否过期，或是否对应当前 OVERLEAF_HOST。"
        )
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise click.ClickException(f"调用 {url} 失败：{exc}") from exc

    final_url = str(getattr(resp, "url", ""))
    if "/login" in final_url.lower():
        raise click.ClickException(
            "请求被重定向到登录页。请检查 OVERLEAF_COOKIE 是否过期。"
        )

    try:
        data = resp.json()
    except ValueError as exc:
        snippet = resp.text[:300].replace("\n", " ")
        raise click.ClickException(
            "接口未返回 JSON，可能是登录态异常或实例接口变更。"
            f"\nURL: {final_url or url}\n响应片段: {snippet}"
        ) from exc

    if not isinstance(data, dict):
        raise click.ClickException("项目列表接口返回结构异常（期望 object）。")
    return data


def _list_projects(api: Api) -> list[dict[str, str]]:
    """获取项目列表，优先 pyoverleaf，失败后回退到 /user/projects。"""
    errors: list[str] = []

    try:
        projects = api.get_projects()
        parsed: list[dict[str, str]] = []
        for project in projects:
            project_id = getattr(project, "id", None)
            project_name = getattr(project, "name", None)
            if isinstance(project_id, str) and isinstance(project_name, str):
                parsed.append({"id": project_id, "name": project_name})
        if parsed:
            return parsed
        errors.append("api.get_projects 返回空列表。")
    except Exception as exc:
        errors.append(f"api.get_projects 失败：{exc}")

    try:
        payload = _fetch_user_projects_json(api)
        raw_projects = payload.get("projects")
        if not isinstance(raw_projects, list):
            raise click.ClickException("项目列表接口返回缺少 projects 数组。")

        parsed = []
        for item in raw_projects:
            if not isinstance(item, dict):
                continue
            project_id = item.get("_id")
            project_name = item.get("name")
            if isinstance(project_id, str) and isinstance(project_name, str):
                parsed.append({"id": project_id, "name": project_name})

        if parsed:
            return parsed
        errors.append("/user/projects 返回空列表。")
    except click.ClickException as exc:
        errors.append(str(exc))

    raise click.ClickException("获取项目列表失败：\n- " + "\n- ".join(errors))


def _build_clone_url(raw_url: str, user: str = "git") -> str:
    """构造带用户名的克隆地址，例如 https://git@host/git/<id>。"""
    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise click.ClickException(f"Git URL 无效：{raw_url}")
    if "@" in parsed.netloc or not user:
        return raw_url
    return urlunparse(parsed._replace(netloc=f"{user}@{parsed.netloc}"))


def _resolve_project(api: Api, project_name_or_id: str) -> tuple[str, str]:
    """将项目名或项目 ID 解析为 (project_id, project_name)。"""
    projects = _list_projects(api)
    for project in projects:
        if project["name"] == project_name_or_id or project["id"] == project_name_or_id:
            return project["id"], project["name"]

    names = ", ".join(p["name"] for p in projects)
    raise click.ClickException(
        f"项目 '{project_name_or_id}' 不存在。当前可用项目：{names}"
    )


def _review_get(
    api: Api, project_id: str, suffix: str, *, expected_json: bool = True
) -> Any:
    """调用 review GET 接口，兼容不同部署路径。"""
    candidates = [
        f"https://{api._host}/project/{project_id}/{suffix}",
        f"https://{api._host}/chat/project/{project_id}/{suffix}",
    ]
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
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
        except Exception as exc:
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
        f"https://{api._host}/project/{project_id}/{suffix}",
        f"https://{api._host}/chat/project/{project_id}/{suffix}",
    ]
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
    csrf = api._get_csrf_token(project_id)
    headers = {
        "Referer": f"https://{api._host}/project/{project_id}",
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
        except Exception as exc:
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
        socket = api._open_socket(project_id)
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
            except Exception:
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
    """基于 doc comments 原生数据构建 thread -> doc/path 映射。"""
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


@cli.group("git")
def cmd_git():
    """Git 集成相关命令。"""


@cmd_git.command("urls")
@click.option("--compact", is_flag=True, help="使用紧凑 JSON 输出（默认为带缩进）。")
@click.option(
    "--base-url",
    help="可选。指定 Git 地址基础前缀（默认: https://<OVERLEAF_HOST>/git）。",
)
@click.option(
    "--clone-user",
    default="git",
    show_default=True,
    help="克隆地址中的认证用户名。",
)
def cmd_git_urls(compact: bool, base_url: str | None, clone_user: str):
    """获取当前账号每个项目的 Git 地址。"""
    api = _build_api()
    projects = _list_projects(api)
    default_base_url = f"https://{api._host}/git"
    resolved_base_url = (base_url or default_base_url).rstrip("/")

    rows: list[dict[str, Any]] = []
    for project in projects:
        raw_git_url = f"{resolved_base_url}/{project['id']}"
        rows.append(
            {
                "project_id": project["id"],
                "project_name": project["name"],
                "git_url": raw_git_url,
                "git_clone_url": _build_clone_url(raw_git_url, clone_user),
            }
        )

    print(
        json.dumps(
            {
                "host": api._host,
                "git_base_url": resolved_base_url,
                "project_count": len(rows),
                "projects": rows,
            },
            ensure_ascii=False,
            indent=None if compact else 2,
        )
    )


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

    new_threads = _fetch_review_threads(api, project_id)
    new_thread = new_threads.get(thread_id)
    is_resolved = isinstance(new_thread, dict) and bool(new_thread.get("resolved"))
    if not is_resolved:
        raise click.ClickException(
            f"线程 {thread_id} 请求已发送，但复查仍未标记 resolved。请在网页端确认权限或状态。"
        )
    print(f"项目 '{project_name}' 线程 {thread_id} 已标记为 resolved。")


# ─── Create Project ───────────────────────────────────────────────────────────


def _create_project(
    api: Api,
    project_name: str,
    *,
    template: str = "none",
) -> dict[str, Any]:
    """通过 /project/new 接口创建新项目。

    template: "none"（空白项目）或 "example"（示例项目）。
    返回接口响应 JSON（含 project_id）。
    """
    url = f"https://{api._host}/project/new"
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)

    # 获取 CSRF token — 需要先访问一个项目页面或首页
    # pyoverleaf 的 _get_csrf_token 需要 project_id，这里我们直接从首页获取
    csrf = _get_csrf_token_from_home(api)

    headers = {
        "Referer": f"https://{api._host}/project",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-csrf-token": csrf,
    }
    request_kwargs["headers"] = headers

    body: dict[str, Any] = {"projectName": project_name}
    if template == "example":
        body["template"] = "example"

    resp = session.post(url, json=body, **request_kwargs)
    if resp.status_code in {401, 403}:
        raise click.ClickException("认证失败（401/403）。请检查 OVERLEAF_COOKIE 是否过期。")
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise click.ClickException(f"创建项目失败：{exc}") from exc

    try:
        return resp.json()
    except ValueError as exc:
        snippet = resp.text[:300].replace("\n", " ")
        raise click.ClickException(f"创建项目接口未返回 JSON。响应片段: {snippet}") from exc


def _get_csrf_token_from_home(api: Api) -> str:
    """从 Overleaf 首页或 /project 页面获取 CSRF token。"""
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
    request_kwargs.pop("headers", None)

    url = f"https://{api._host}/project"
    resp = session.get(url, **request_kwargs)
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise click.ClickException(f"获取 CSRF token 失败：{exc}") from exc

    import re
    # Overleaf 将 CSRF token 嵌入页面 meta 标签或 JS 变量中
    # 常见模式：<meta name="ol-csrfToken" content="...">
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    if not match:
        # 也可能是 window.csrfToken = "...";
        match = re.search(r'csrfToken["\']?\s*[:=]\s*["\']([^"\'\ ]+)', resp.text)
    if not match:
        raise click.ClickException(
            "无法从页面中提取 CSRF token。Cookie 可能已过期或页面结构已变更。"
        )
    return match.group(1)


@cli.command("create")
@click.argument("project_name")
@click.option(
    "--template",
    type=click.Choice(["none", "example"]),
    default="none",
    show_default=True,
    help="项目模板：none（空白）或 example（Overleaf 示例项目）。",
)
@click.option("--compact", is_flag=True, help="使用紧凑 JSON 输出。")
def cmd_create(project_name: str, template: str, compact: bool):
    """创建新的 Overleaf 项目。"""
    api = _build_api()

    print(f"正在创建项目 '{project_name}'...", file=sys.stderr)
    data = _create_project(api, project_name, template=template)

    project_id = data.get("project_id") or data.get("_id") or data.get("id")
    if not project_id:
        raise click.ClickException(f"创建成功但未返回 project_id。响应: {json.dumps(data)}")

    git_url = f"https://{api._host}/git/{project_id}"
    clone_url = _build_clone_url(git_url, "git")

    result = {
        "project_id": project_id,
        "project_name": project_name,
        "template": template,
        "git_url": git_url,
        "git_clone_url": clone_url,
        "web_url": f"https://{api._host}/project/{project_id}",
    }

    print(json.dumps(result, ensure_ascii=False, indent=None if compact else 2))


# ─── Compile ──────────────────────────────────────────────────────────────────


def _set_compiler(api: Api, project_id: str, compiler: str) -> None:
    """通过 Overleaf settings API 设置项目编译器。"""
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
    # 从项目页获取 CSRF token（meta 标签格式）
    resp = session.get(f"https://{api._host}/project/{project_id}", **request_kwargs)
    import re
    m = re.search(r'ol-csrfToken.*?content="([^"]+)"', resp.text)
    if not m:
        # 回退到 pyoverleaf 内置方法
        csrf = api._get_csrf_token(project_id)
    else:
        csrf = m.group(1)
    headers = {
        "Referer": f"https://{api._host}/project/{project_id}",
        "Content-Type": "application/json",
        "x-csrf-token": csrf,
    }
    request_kwargs["headers"] = headers
    resp2 = session.post(
        f"https://{api._host}/project/{project_id}/settings",
        json={"compiler": compiler},
        **request_kwargs,
    )
    if resp2.status_code not in {200, 204}:
        print(f"警告：设置编译器为 {compiler} 失败（HTTP {resp2.status_code}）", file=sys.stderr)
    else:
        print(f"编译器已设置为 {compiler}", file=sys.stderr)


def _compile_project(api: Api, project_id: str, compiler: str | None = None) -> dict[str, Any]:
    """触发项目编译，返回 compile 接口响应 JSON。

    若指定 compiler（如 xelatex / pdflatex / lualatex），会先通过 settings API 设置编译器。
    """
    if compiler:
        _set_compiler(api, project_id, compiler)

    url = f"https://{api._host}/project/{project_id}/compile?enable_pdf_caching=true"
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
    csrf = api._get_csrf_token(project_id)
    headers = {
        "Referer": f"https://{api._host}/project/{project_id}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-csrf-token": csrf,
    }
    request_kwargs["headers"] = headers

    body = {
        "rootDoc_id": None,
        "draft": False,
        "check": "silent",
        "incrementalCompilesEnabled": True,
    }

    resp = session.post(url, json=body, **request_kwargs)
    if resp.status_code in {401, 403}:
        raise click.ClickException("认证失败（401/403）。请检查 OVERLEAF_COOKIE 是否过期。")
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise click.ClickException(f"编译请求失败：{exc}") from exc

    try:
        return resp.json()
    except ValueError as exc:
        snippet = resp.text[:300].replace("\n", " ")
        raise click.ClickException(f"编译接口未返回 JSON。响应片段: {snippet}") from exc


@cli.command("compile")
@click.argument("project")
@click.option("--compact", is_flag=True, help="使用紧凑 JSON 输出（默认为带缩进）。")
@click.option("--compiler", "-c", default=None, type=click.Choice(["xelatex", "pdflatex", "lualatex"]), help="编译引擎（默认使用项目已有设置）。")
def cmd_compile(project: str, compact: bool, compiler: str | None):
    """触发项目 PDF 编译，输出编译结果（状态、PDF 地址、输出文件列表）。"""
    api = _build_api()
    project_id, project_name = _resolve_project(api, project)

    print(f"正在编译项目 '{project_name}'...", file=sys.stderr)
    data = _compile_project(api, project_id, compiler=compiler)

    status = data.get("status", "unknown")
    output_files = data.get("outputFiles", [])
    pdf_file = next((f for f in output_files if f.get("type") == "pdf"), None)

    result: dict[str, Any] = {
        "project": {"id": project_id, "name": project_name},
        "status": status,
        "pdf_url": f"https://{api._host}{pdf_file['url']}" if pdf_file else None,
        "output_files": [
            {
                "path": f.get("path"),
                "type": f.get("type"),
                "url": f"https://{api._host}{f['url']}",
            }
            for f in output_files
        ],
    }

    print(
        json.dumps(result, ensure_ascii=False, indent=None if compact else 2)
    )

    if status != "success":
        sys.exit(1)


@cli.command("pdf")
@click.argument("project")
@click.option("--output", "-o", default=None, help="输出 PDF 文件路径（默认：<项目名>.pdf）。")
@click.option("--compiler", "-c", default=None, type=click.Choice(["xelatex", "pdflatex", "lualatex"]), help="编译引擎（默认使用项目已有设置）。")
@click.option("--compile", "do_compile", is_flag=True, default=True, hidden=True)
def cmd_pdf(project: str, output: str | None, compiler: str | None, do_compile: bool):
    """编译项目并下载 PDF 到本地。"""
    api = _build_api()
    project_id, project_name = _resolve_project(api, project)

    print(f"正在编译项目 '{project_name}'...", file=sys.stderr)
    data = _compile_project(api, project_id, compiler=compiler)

    status = data.get("status", "unknown")
    if status != "success":
        output_files = data.get("outputFiles", [])
        log_file = next((f for f in output_files if f.get("type") == "log"), None)
        hint = ""
        if log_file:
            hint = f"\n编译日志可通过以下地址查看：https://{api._host}{log_file['url']}"
        raise click.ClickException(f"编译失败，状态：{status}。{hint}")

    output_files = data.get("outputFiles", [])
    pdf_file = next((f for f in output_files if f.get("type") == "pdf"), None)
    if not pdf_file:
        raise click.ClickException("编译成功但未找到 PDF 输出文件。")

    pdf_url = f"https://{api._host}{pdf_file['url']}"

    # 下载 PDF
    session = api._get_session()
    request_kwargs = dict(api._request_kwargs)
    request_kwargs["headers"] = {
        "Referer": f"https://{api._host}/project/{project_id}",
    }

    print(f"正在下载 PDF：{pdf_url}", file=sys.stderr)
    resp = session.get(pdf_url, **request_kwargs)
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise click.ClickException(f"PDF 下载失败：{exc}") from exc

    # 确定输出路径
    if output is None:
        safe_name = project_name.replace("/", "_").replace("\\", "_")
        output = f"{safe_name}.pdf"

    pathlib.Path(output).write_bytes(resp.content)
    print(f"PDF 已保存：{output}")


if __name__ == "__main__":
    cli()
