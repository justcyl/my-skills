#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""外部仓库浅克隆工具。

将 GitHub 仓库浅克隆到本地临时目录，删除 .git 以减小体积。
支持多种 GitHub URL 格式和 owner/repo 简写。
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys

# 默认存储目录
DEFAULT_OUTPUT_DIR = os.environ.get("EXTRACT_REPO_DIR", "/tmp/external-repos")

# GitHub URL 匹配模式
_OWNER_REPO_RE = re.compile(r"^([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)$")
_HTTPS_RE = re.compile(
    r"^https?://github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+?)"
    r"(?:\.git)?(?:/(?:tree|blob)/([^/]+)(?:/.*)?)?\s*$",
)
_SSH_RE = re.compile(
    r"^git@github\.com:([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+?)(?:\.git)?$"
)


def normalize_github_url(raw: str) -> tuple[str, str, str | None]:
    """将各种 GitHub URL 格式归一化。

    Args:
        raw: GitHub URL 或 owner/repo 简写。

    Returns:
        (clone_url, dir_name, branch) 元组。branch 为 None 时使用默认分支。

    Raises:
        ValueError: 无法识别的 URL 格式。
    """
    # owner/repo 简写
    m = _OWNER_REPO_RE.match(raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        return f"https://github.com/{owner}/{repo}.git", f"{owner}-{repo}", None

    # HTTPS URL（含 tree/blob 路径）
    m = _HTTPS_RE.match(raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        branch = m.group(3)  # 可能为 None
        return f"https://github.com/{owner}/{repo}.git", f"{owner}-{repo}", branch

    # SSH URL
    m = _SSH_RE.match(raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        return f"https://github.com/{owner}/{repo}.git", f"{owner}-{repo}", None

    raise ValueError(f"无法识别的 GitHub URL 格式: {raw}")


def _unique_dir(base: pathlib.Path, name: str) -> pathlib.Path:
    """生成不冲突的目录路径。同名时追加数字后缀。

    Args:
        base: 父目录。
        name: 期望的目录名。

    Returns:
        唯一的目标路径。
    """
    target = base / name
    if not target.exists():
        return target
    i = 2
    while True:
        candidate = base / f"{name}-{i}"
        if not candidate.exists():
            return candidate
        i += 1


def clone_repo(
    clone_url: str,
    target_dir: pathlib.Path,
    branch: str | None = None,
    dry_run: bool = False,
) -> pathlib.Path:
    """浅克隆仓库到指定目录。

    Args:
        clone_url: Git 克隆 URL。
        target_dir: 目标目录。
        branch: 可选的分支名。
        dry_run: 仅打印操作计划。

    Returns:
        实际克隆到的目录路径。
    """
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([clone_url, str(target_dir)])

    if dry_run:
        print(f"[dry-run] 将执行: {' '.join(cmd)}")
        print(f"[dry-run] 目标目录: {target_dir}")
        return target_dir

    print(f"正在克隆 {clone_url} ...")
    subprocess.run(cmd, check=True)

    # 删除 .git 目录以减小体积
    git_dir = target_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
        print("已删除 .git 目录")

    print(f"完成: {target_dir}")
    return target_dir


def list_repos(base_dir: pathlib.Path) -> None:
    """列出已下载的仓库目录。

    Args:
        base_dir: 存储根目录。
    """
    if not base_dir.exists():
        print("暂无已下载的仓库。")
        return

    dirs = sorted(base_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    dirs = [d for d in dirs if d.is_dir()]

    if not dirs:
        print("暂无已下载的仓库。")
        return

    print(f"已下载的仓库 ({base_dir}):\n")
    for d in dirs:
        # 计算目录大小（MB）
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        size_mb = size / (1024 * 1024)
        print(f"  {d.name:<40} {size_mb:>8.1f} MB")


def cleanup_repo(base_dir: pathlib.Path, name: str) -> None:
    """清理指定仓库目录。

    Args:
        base_dir: 存储根目录。
        name: 仓库目录名。
    """
    target = base_dir / name
    if not target.exists():
        print(f"目录不存在: {target}", file=sys.stderr)
        sys.exit(1)
    shutil.rmtree(target)
    print(f"已清理: {target}")


def cleanup_all(base_dir: pathlib.Path) -> None:
    """清理所有已下载仓库。

    Args:
        base_dir: 存储根目录。
    """
    if not base_dir.exists():
        print("暂无需要清理的仓库。")
        return
    shutil.rmtree(base_dir)
    print(f"已清理全部: {base_dir}")


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(
        description="外部仓库浅克隆工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  %(prog)s vercel/next.js
  %(prog)s https://github.com/vercel/next.js
  %(prog)s https://github.com/vercel/next.js/tree/canary
  %(prog)s --list
  %(prog)s --cleanup vercel-next.js
  %(prog)s --dry-run owner/repo""",
    )

    parser.add_argument("repo", nargs="?", help="GitHub URL 或 owner/repo 简写")
    parser.add_argument("--branch", "-b", default=None, help="指定分支（默认：仓库默认分支）")
    parser.add_argument(
        "--output-dir",
        "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录（默认：{DEFAULT_OUTPUT_DIR}）",
    )
    parser.add_argument("--list", action="store_true", help="列出已下载的仓库")
    parser.add_argument("--cleanup", metavar="NAME", help="清理指定仓库目录")
    parser.add_argument("--cleanup-all", action="store_true", help="清理所有已下载仓库")
    parser.add_argument("--dry-run", action="store_true", help="仅显示操作计划，不执行")

    args = parser.parse_args()
    base_dir = pathlib.Path(args.output_dir)

    # 管理命令
    if args.list:
        list_repos(base_dir)
        return

    if args.cleanup:
        cleanup_repo(base_dir, args.cleanup)
        return

    if args.cleanup_all:
        cleanup_all(base_dir)
        return

    # 克隆操作
    if not args.repo:
        parser.error("请提供 GitHub URL 或 owner/repo")

    # 检查 git 是否可用
    if not shutil.which("git"):
        print("错误: 未找到 git 命令，请先安装 git。", file=sys.stderr)
        sys.exit(1)

    try:
        clone_url, dir_name, url_branch = normalize_github_url(args.repo)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # CLI --branch 优先于 URL 中解析出的 branch
    branch = args.branch or url_branch

    base_dir.mkdir(parents=True, exist_ok=True)
    target_dir = _unique_dir(base_dir, dir_name)

    result = clone_repo(clone_url, target_dir, branch=branch, dry_run=args.dry_run)

    # 输出绝对路径，方便管道使用
    print(result.resolve())


if __name__ == "__main__":
    main()
