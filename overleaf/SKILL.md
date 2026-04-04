---
name: overleaf
description: 通过 Git 和 Review API 与 Overleaf 项目交互。当用户需要创建新项目、克隆、编辑并推送 Overleaf 项目，或查看、定位、解决 review 评论线程，或触发编译、下载 PDF 时使用。
---

# Overleaf Skill

通过 Git 协议操作 Overleaf 项目文件（克隆、拉取、编辑、提交、推送），通过 REST API 创建新项目，通过 Review API 管理评论线程（列出、解决），通过 Compile API 触发远程编译并下载 PDF。

所有文件级操作（浏览目录、读写文件、创建删除、下载项目）统一通过 `git clone`/`git pull` + 本地编辑 + `git push` 完成，不再使用 WebSocket/REST 逐文件操作。

## 环境准备

### 获取 overleaf 认证信息

需要以下环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `OVERLEAF_HOST` | Overleaf 实例域名（不含 `https://`） | `overleaf.mycompany.com` 或 `www.overleaf.com` |
| `OVERLEAF_COOKIE` | 浏览器 Cookie 头部字符串 | `overleaf_session2=s%3Axxx; gke-route=yyy` |

在操作前先确认用户是否已经配置好了环境变量，若无需按照以下步骤获取：
获取 Cookie：浏览器打开 Overleaf → F12 → Network → 任意请求 → Request Headers → Cookie。

```bash
export OVERLEAF_HOST="overleaf.mycompany.com"
export OVERLEAF_COOKIE="overleaf_session2=s%3Axxx; gke-route=yyy"
```

### Git 认证信息

Git 凭据默认已配置在 osxkeychain 中，可直接使用 `git clone https://...`。

若失败，提示用户配置相关 token。

## 调用方式

Review/获取项目对应 git 地址 的操作通过 wrapper 脚本：

```bash
bash scripts/ol.sh <命令> [参数]
```

获取 git url后，直接使用 `git` 命令行进行管理。

## 命令参考

### 创建新项目

```bash
# 创建空白项目
bash scripts/ol.sh create "My New Paper"

# 创建带 Overleaf 示例内容的项目
bash scripts/ol.sh create "My New Paper" --template example

# 紧凑 JSON 输出
bash scripts/ol.sh create "My New Paper" --compact
```

输出字段：`project_id`、`project_name`、`template`、`git_url`、`git_clone_url`、`web_url`。

### 获取项目 Git 地址

```bash
# 列出所有项目及其 Git 地址（带缩进 JSON）
bash scripts/ol.sh git urls

# 紧凑 JSON（便于管道处理）
bash scripts/ol.sh git urls --compact

# 覆盖默认 Git 地址前缀
bash scripts/ol.sh git urls --base-url "https://git.example.com"
```

输出字段：`project_id`、`project_name`、`git_url`、`git_clone_url`。

### 获取 review 评论线程

```bash
# 带缩进 JSON
bash scripts/ol.sh review list "MyProject"

# 紧凑 JSON
bash scripts/ol.sh review list "MyProject" --compact
```

### 解决 review 线程

```bash
# 使用线程首条消息用户作为 resolve 用户
bash scripts/ol.sh review resolve "MyProject" "69c2745dc0f84b044e000001"

# 显式指定 user_id
bash scripts/ol.sh review resolve "MyProject" "69c2745dc0f84b044e000001" --user-id "69a65a7a8f69a4e6b57d0ddd"
```

### 编译项目

```bash
# 触发编译，输出带缩进 JSON（含状态、PDF 地址、所有输出文件）
bash scripts/ol.sh compile "MyProject"

# 紧凑 JSON（便于管道处理）
bash scripts/ol.sh compile "MyProject" --compact
```

输出字段：`status`（`success` / `failure` / `error`）、`pdf_url`、`output_files`（含 `.pdf`、`.log`、`.bbl` 等）。

### 编译并下载 PDF

```bash
# 编译并下载 PDF，文件名默认为 <项目名>.pdf
bash scripts/ol.sh pdf "MyProject"

# 指定输出路径
bash scripts/ol.sh pdf "MyProject" --output /tmp/paper.pdf
```

## 典型工作流

### 创建项目并开始编辑

```bash
# 1. 创建新项目
bash scripts/ol.sh create "My New Paper"

# 2. 从输出中获取 git_clone_url，克隆到本地
git clone https://git@overleaf.mycompany.com/git/<project_id> /tmp/my-new-paper

# 3. 编辑文件
# ...编辑 /tmp/my-new-paper/main.tex

# 4. 提交并推送
cd /tmp/my-new-paper
git add -A
git commit -m "initial content"
git push
```

### 克隆并编辑项目

```bash
# 1. 获取项目 Git 地址
bash scripts/ol.sh git urls

# 2. 克隆项目到本地
git clone https://git@overleaf.mycompany.com/git/<project_id> /tmp/my-project

# 3. 本地编辑文件
# ...编辑 /tmp/my-project/main.tex 等

# 4. 提交并推送
cd /tmp/my-project
git add -A
git commit -m "update content"
git push
```

### 在已克隆的项目中同步他人更改

当项目已经克隆到本地，提交前需要先拉取协作者的最新更改：

```bash
cd /tmp/my-project

# 拉取远端最新更改（rebase 避免产生多余的 merge commit）
git pull --rebase

# 若有冲突，解决后继续
git add -A
git rebase --continue

# 推送本地修改
git push
```

### 处理 review 评论

```bash
# 1. 查看所有 review
bash scripts/ol.sh review list "MyProject"

# 2. 克隆项目到本地
git clone https://git@overleaf.mycompany.com/git/<project_id> /tmp/my-project

# 3. 根据 review 位置信息，在本地编辑对应文件

# 4. 推送修改
cd /tmp/my-project
git add -A
git commit -m "address review comments"
git push

# 5. 解决已处理的 review
bash scripts/ol.sh review resolve "MyProject" "<thread_id>"
```

### 编译并获取 PDF

```bash
# 1. 推送最新修改
cd /tmp/my-project
git add -A && git commit -m "final edits" && git push

# 2. 编译并下载 PDF
bash /path/to/scripts/ol.sh pdf "MyProject"

# 3. 或先确认编译状态，再手动下载
bash /path/to/scripts/ol.sh compile "MyProject"
# 得到 pdf_url 后：
curl -L -b "$OVERLEAF_COOKIE" "<pdf_url>" -o paper.pdf
```

## 已知限制

- Cookie 认证依赖浏览器登录状态，过期后需重新获取
- `review list/resolve` 依赖 Overleaf 内部评论线程与 `joinDoc` 接口（非官方公开 API），不同私有部署可能有差异
- `compile` / `pdf` 依赖 `POST /project/{id}/compile` 接口（非官方公开 API），不同私有部署可能有差异
- `git urls` 依赖 `GET /user/projects` 接口；若实例关闭或 Cookie 无权限会返回 401/403
- Git 推送后 Overleaf 编辑器需刷新页面才能看到更新

## 依赖

- `pyoverleaf`：通过 `uv tool install pyoverleaf` 安装（仅 review 功能需要）
- Python 解释器路径：`~/.local/share/uv/tools/pyoverleaf/bin/python`
- `git`：系统 Git 客户端，凭据已配置在 osxkeychain
