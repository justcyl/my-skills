# gh API 速查 — 仓库探索

通过 `gh api` 探索外部 GitHub 仓库的常用命令。所有命令中的 `owner/repo` 需替换为实际值。

## 仓库元数据

```bash
# 基本信息
gh api repos/owner/repo | jq '{
  description, language, topics,
  stars: .stargazers_count,
  forks: .forks_count,
  default_branch,
  size,
  license: .license.spdx_id,
  created_at, updated_at
}'

# 仓库大小（KB），用于判断是否适合克隆
gh api repos/owner/repo --jq '.size'

# 语言分布
gh api repos/owner/repo/languages
```

## README

```bash
# 获取 README 内容
gh api repos/owner/repo/readme --jq '.content' | base64 -d

# 获取 README 元信息（路径、大小）
gh api repos/owner/repo/readme --jq '{name, path, size}'
```

## 文件树

```bash
# 递归获取整个文件树（使用默认分支）
gh api "repos/owner/repo/git/trees/main?recursive=1" | \
  jq -r '.tree[] | select(.type == "blob") | .path'

# 仅显示前 100 个文件
gh api "repos/owner/repo/git/trees/main?recursive=1" | \
  jq -r '.tree[] | select(.type == "blob") | .path' | head -100

# 按扩展名过滤
gh api "repos/owner/repo/git/trees/main?recursive=1" | \
  jq -r '.tree[] | select(.type == "blob") | .path' | grep '\.py$'

# 仅列出顶层目录结构
gh api "repos/owner/repo/git/trees/main" | \
  jq -r '.tree[] | "\(.type)\t\(.path)"'
```

## 读取文件内容

```bash
# 读取单个文件（自动 base64 解码）
gh api repos/owner/repo/contents/path/to/file --jq '.content' | base64 -d

# 读取指定分支上的文件
gh api "repos/owner/repo/contents/path/to/file?ref=develop" --jq '.content' | base64 -d

# 列出某个目录下的文件
gh api repos/owner/repo/contents/src --jq '.[] | "\(.type)\t\(.name)"'
```

## 提交历史

```bash
# 最近 5 条提交
gh api repos/owner/repo/commits --jq \
  '.[0:5] | .[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'

# 某个路径的提交历史
gh api "repos/owner/repo/commits?path=src/main.py" --jq \
  '.[0:5] | .[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'

# 带日期的提交
gh api repos/owner/repo/commits --jq \
  '.[0:10] | .[] | "\(.commit.author.date[0:10]) \(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

## 搜索代码

```bash
# 在仓库内搜索代码（需要 URL 编码）
gh api "search/code?q=useState+repo:owner/repo+language:typescript" --jq \
  '.items[0:5] | .[] | "\(.path):\(.name)"'

# 搜索文件名
gh api "search/code?q=filename:config.ts+repo:owner/repo" --jq \
  '.items[] | .path'
```

## Release 和 Tag

```bash
# 最新 Release
gh api repos/owner/repo/releases/latest --jq '{tag_name, name, published_at, body}'

# 最近 5 个 Release
gh api repos/owner/repo/releases --jq \
  '.[0:5] | .[] | "\(.tag_name)\t\(.published_at[0:10])\t\(.name)"'

# 所有 Tag
gh api repos/owner/repo/tags --jq '.[0:10] | .[] | .name'
```

## 分支和 PR

```bash
# 列出分支
gh api repos/owner/repo/branches --jq '.[0:10] | .[] | .name'

# 最近的 PR
gh api repos/owner/repo/pulls --jq \
  '.[0:5] | .[] | "#\(.number) \(.title) [\(.state)]"'
```

## Issue

```bash
# 最近的 Issue
gh api repos/owner/repo/issues --jq \
  '.[0:10] | .[] | "#\(.number) \(.title) [\(.state)]"'

# 按标签过滤
gh api "repos/owner/repo/issues?labels=bug" --jq \
  '.[0:5] | .[] | "#\(.number) \(.title)"'
```

## 贡献者

```bash
# 贡献者排行（前 10）
gh api repos/owner/repo/contributors --jq \
  '.[0:10] | .[] | "\(.login)\t\(.contributions) commits"'
```

## 速率限制

```bash
# 查看当前 API 速率限制
gh api rate_limit --jq '.rate | "剩余: \(.remaining)/\(.limit)  重置于: \(.reset | todate)"'
```

GitHub API 默认速率限制为认证用户 5000 次/小时。`search/code` 接口限制为 30 次/分钟。
