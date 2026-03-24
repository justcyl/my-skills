#!/usr/bin/env python3
"""
Overleaf CLI 包装器。

通过环境变量认证（而非从浏览器读取 Cookie），支持以下操作：
  ls [PATH]                  列出项目或文件
  read <PROJECT/PATH>        读取文件内容到标准输出
  write <PROJECT/PATH>       从标准输入写入文件
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
    projects = api.get_projects()
    project_id = next((p.id for p in projects if p.name == project_name), None)
    if project_id is None:
        names = ", ".join(p.name for p in projects)
        raise click.ClickException(
            f"项目 '{project_name}' 不存在。当前可用项目：{names}"
        )
    return ProjectIO(api, project_id), rel_path


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
    projects = api.get_projects()
    project_id = next((p.id for p in projects if p.name == project), None)
    if project_id is None:
        names = ", ".join(p.name for p in projects)
        raise click.ClickException(
            f"项目 '{project}' 不存在。当前可用项目：{names}"
        )
    api.download_project(project_id, output_path)
    print(f"项目 '{project}' 已下载到：{output_path}")


if __name__ == "__main__":
    cli()
