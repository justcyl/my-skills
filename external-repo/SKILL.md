---
name: external-repo
description: 研究和探索外部 GitHub 仓库。当需要了解开源项目的架构、API、代码实现或文档时使用。支持 gh CLI、浅克隆两种策略，模型自主选择。
---

# External Repo — 外部仓库研究

研究任意公开 GitHub 仓库的架构、API、代码实现和文档。两种策略可灵活组合。

## 何时使用

- 用户要求了解某个 GitHub 开源项目的架构或设计
- 用户需要查看外部仓库的具体文件或实现细节
- 用户要求对比、评估或学习某个外部仓库
- 用户提供了 GitHub URL 并希望深入理解
- 用户需要从外部项目中提取代码模式或最佳实践

## 策略概览

| 策略 | 适用场景 | 工具 |
|------|---------|------|
| gh CLI | 特定文件查看、README、元数据 | `gh api` + `jq` |
| 本地浅克隆 | 小仓库全面搜索、跨文件 grep、gh CLI 不足时 | `extract_repo.py` |

## 策略选择指南

根据以下信号自主判断，可组合使用多种策略：

| 信号 | 推荐策略 |
|------|---------|
| 需要快速了解仓库概况或文档结构 | gh CLI |
| 需要查看特定文件内容或最近提交 | gh CLI |
| 小仓库 + 需要跨多个文件搜索代码模式 | 本地浅克隆 |
| 需要 grep / ast-grep / fd 搜索 | 本地浅克隆 |
| gh CLI 信息不足，需要更深入分析 | 本地浅克隆 |

## 策略 1：gh CLI 探索

适用于任何有权限访问的 GitHub 仓库。核心命令如下，更多命令见 [gh API 速查](references/gh-api-cheatsheet.md)。

### 核心命令

获取仓库概览：

```bash
gh api repos/owner/repo | jq '{description, language, topics, stars: .stargazers_count, default_branch}'
```

获取 README：

```bash
gh api repos/owner/repo/readme --jq '.content' | base64 -d
```

获取文件树（递归）：

```bash
gh api "repos/owner/repo/git/trees/main?recursive=1" | \
  jq -r '.tree[] | select(.type == "blob") | .path' | head -100
```

读取特定文件：

```bash
gh api repos/owner/repo/contents/path/to/file --jq '.content' | base64 -d
```

查看最近提交：

```bash
gh api repos/owner/repo/commits --jq '.[0:5] | .[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

### 示例场景

- 快速查看某个项目用了什么技术栈 → 获取概览 + README
- 阅读某个配置文件 → 获取文件树定位后读取内容
- 了解最近的变更方向 → 查看最近提交

## 策略 2：本地浅克隆

适用于小型仓库或需要深度搜索的场景。

### 使用方式

```bash
uv run external-repo/scripts/extract_repo.py <github-url-or-owner/repo>
```

支持多种 URL 格式：

```bash
uv run external-repo/scripts/extract_repo.py vercel/next.js
uv run external-repo/scripts/extract_repo.py https://github.com/vercel/next.js
uv run external-repo/scripts/extract_repo.py https://github.com/vercel/next.js/tree/canary
```

### 命令参数

| 参数 | 说明 |
|------|------|
| `repo` | GitHub URL 或 `owner/repo` 简写 |
| `--branch`, `-b` | 指定分支（默认：仓库默认分支） |
| `--output-dir`, `-o` | 输出目录（默认：`/tmp/external-repos`） |
| `--list` | 列出已下载的仓库 |
| `--cleanup NAME` | 清理指定仓库 |
| `--cleanup-all` | 清理所有已下载仓库 |
| `--dry-run` | 仅显示操作计划，不执行 |

### 克隆后操作

```bash
# 进入克隆目录后可用本地工具搜索
fd -e py                           # 查找所有 Python 文件
ast-grep --lang ts -p '$PATTERN'   # 搜索 TS 代码结构
```

### 注意

- 大型仓库（>100MB）建议优先使用 gh CLI
- 克隆产物存放在 `/tmp/external-repos/`，重启后可能丢失
- 完成后可用 `--cleanup` 释放空间

## 限制

- **gh CLI**：需要 GitHub 认证（`gh auth login`）
- **本地克隆**：需要磁盘空间，大仓库耗时较长
- 私有仓库只能使用 gh CLI（需有对应权限）
