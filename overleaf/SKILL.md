---
name: overleaf
description: LaTeX 文档与 Overleaf 项目的首选方案。当需要编写或编辑 .tex 文件、编译 LaTeX 项目并获取 PDF、创建或管理 Overleaf 项目、查看或解决 review 评论时触发。
---

# Overleaf Skill

通过 Git 协议操作 Overleaf 项目文件（克隆、拉取、编辑、提交、推送），通过 REST API 创建新项目，通过 Review API 管理评论线程（列出、解决），通过 Compile API 触发远程编译并下载 PDF。

所有文件级操作（浏览目录、读写文件、创建删除、下载项目）统一通过 `git clone`/`git pull` + 本地编辑 + `git push` 完成，不再使用 WebSocket/REST 逐文件操作。

## Skill 目录结构

`scripts/` 与本 SKILL.md **同级**，位于 SKILL.md 所在目录下：

```
<skill-dir>/          ← 本 SKILL.md 所在目录
├── SKILL.md
└── scripts/
    ├── ol.sh           # 入口：环境准备 + 转发给 ol.py
    ├── ol.py           # CLI 入口：命令解析与调度
    └── edge_cookies.py # 从 Edge 浏览器提取 Cookie
```

**使用前先确定 `SKILL_DIR`**（从 AGENTS.md 中本 skill 的 `<location>` 标签推导）：

```bash
# <location> 示例：/some/path/overleaf/SKILL.md
# → SKILL_DIR=/some/path/overleaf
SKILL_DIR="$(dirname "$(grep -A1 'name: overleaf' ~/.pi/agent/AGENTS.md | grep location | sed 's/.*<location>\(.*\)\/SKILL.md.*/\1/')")"
# 或直接手动赋值为 <location> 去掉末尾 /SKILL.md 后的路径
```

> ⚠️ **始终用 `$SKILL_DIR/scripts/ol.sh` 调用**，不要使用 `~/scripts/` 或其他猜测路径。

## 环境准备

### 获取 overleaf 认证信息

Cookie 支持自动获取：当 `OVERLEAF_COOKIE` 环境变量未设置时，`ol.sh` 会自动从 macOS Edge 浏览器提取对应域名的 Cookie（需要 Edge 已登录 Overleaf）。

因此**通常只需设置 `OVERLEAF_HOST`**，Cookie 会自动处理。推荐在
`~/.config/overleaf/config.env` 中保留域名选择；`ol.sh` 会自动加载该文件：

```bash
# 官方 Overleaf（当前选择）
OVERLEAF_HOST="www.overleaf.com"

# 自托管实例（需要时与上一行互换注释）
# OVERLEAF_HOST="overleaf.cyl.qzz.io"
```

| 变量名 | 说明 | 是否必须 |
|--------|------|----------|
| `OVERLEAF_HOST` | Overleaf 实例域名（不含 `https://`） | 是（默认 `www.overleaf.com`） |
| `OVERLEAF_COOKIE` | 浏览器 Cookie 头部字符串 | 否（未设置时自动从 Edge 获取） |

自动获取会按浏览器规则读取目标主机及其父域 Cookie（例如
`www.overleaf.com` 会同时读取 `.overleaf.com` 的会话 Cookie），并依赖 macOS
Keychain 授权（首次会弹窗确认）。若自动获取失败，可手动设置：
获取 Cookie：浏览器打开 Overleaf → F12 → Network → 任意请求 → Request Headers → Cookie。

```bash
export OVERLEAF_COOKIE="overleaf_session2=s%3Axxx; gke-route=yyy"
```

### Git 认证信息

Git 认证与网页/API Cookie 是两套独立凭据。Git 使用系统配置的
`osxkeychain` credential helper；每个域名仍需单独保存 Git token，不能从 Edge
网页 Cookie 推导或复用。官方站点使用 `git.overleaf.com`，自托管实例通常使用
`<OVERLEAF_HOST>/git`。

若 `git clone` 提示认证失败，需要先为对应 Git 域名配置 token。网页 Cookie
自动读取成功不代表 Git token 已配置。

### WSL/自托管实例的账号登录

如果 Overleaf 服务部署在 WSL，且实例使用本地邮箱/密码认证（`EXTERNAL_AUTH=none`），可以直接使用已有 Overleaf 账号自动获取会话 Cookie，不需要读取 Windows Edge Cookie：

```bash
export OVERLEAF_HOST="overleaf.example.com"
export OVERLEAF_EMAIL="your-existing-account@example.com"
export OVERLEAF_PASSWORD_FILE="$HOME/.config/overleaf/password"
```

密码文件必须设置为 `600`。也可以使用 `OVERLEAF_PASSWORD_COMMAND` 从 `pass` 等凭据管理器读取密码。`ol.sh` 会自动登录、缓存短期会话，并在会话过期后重新登录。

## 调用方式

Review/获取项目对应 git 地址 的操作通过 wrapper 脚本：

```bash
bash "$SKILL_DIR/scripts/ol.sh" <命令> [参数]
```

> Cookie 会自动从 Edge 浏览器获取，无需手动 source 或设置环境变量。

获取 git url后，直接使用 `git` 命令行进行管理。

## 命令参考

### 创建新项目

```bash
# 创建空白项目
bash "$SKILL_DIR/scripts/ol.sh" create "My New Paper"

# 创建带 Overleaf 示例内容的项目
bash "$SKILL_DIR/scripts/ol.sh" create "My New Paper" --template example

# 紧凑 JSON 输出
bash "$SKILL_DIR/scripts/ol.sh" create "My New Paper" --compact
```

输出字段：`project_id`、`project_name`、`template`、`git_url`、`git_clone_url`、`web_url`。

### 获取项目 Git 地址

```bash
# 列出所有项目及其 Git 地址（带缩进 JSON）
bash "$SKILL_DIR/scripts/ol.sh" git urls

# 紧凑 JSON（便于管道处理）
bash "$SKILL_DIR/scripts/ol.sh" git urls --compact

# 覆盖默认 Git 地址前缀（官方默认 https://git.overleaf.com）
bash "$SKILL_DIR/scripts/ol.sh" git urls --base-url "https://git.example.com"
```

输出字段：`project_id`、`project_name`、`git_url`、`git_clone_url`。

### 获取 review 评论线程

```bash
# 带缩进 JSON
bash "$SKILL_DIR/scripts/ol.sh" review list "MyProject"

# 紧凑 JSON
bash "$SKILL_DIR/scripts/ol.sh" review list "MyProject" --compact
```

### 解决 review 线程

```bash
# 使用线程首条消息用户作为 resolve 用户
bash "$SKILL_DIR/scripts/ol.sh" review resolve "MyProject" "69c2745dc0f84b044e000001"

# 显式指定 user_id
bash "$SKILL_DIR/scripts/ol.sh" review resolve "MyProject" "69c2745dc0f84b044e000001" --user-id "69a65a7a8f69a4e6b57d0ddd"
```

### 编译项目

```bash
# 触发编译，输出带缩进 JSON（含状态、PDF 地址、所有输出文件）
bash "$SKILL_DIR/scripts/ol.sh" compile "MyProject"

# 紧凑 JSON（便于管道处理）
bash "$SKILL_DIR/scripts/ol.sh" compile "MyProject" --compact

# 指定编译引擎（xelatex / pdflatex / lualatex）
bash "$SKILL_DIR/scripts/ol.sh" compile "MyProject" --compiler xelatex
```

输出字段：`status`（`success` / `failure` / `error`）、`pdf_url`、`output_files`（含 `.pdf`、`.log`、`.bbl` 等）。

### 编译并下载 PDF

```bash
# 编译并下载 PDF，文件名默认为 <项目名>.pdf
bash "$SKILL_DIR/scripts/ol.sh" pdf "MyProject"

# 指定输出路径
bash "$SKILL_DIR/scripts/ol.sh" pdf "MyProject" --output /tmp/paper.pdf

# 指定编译引擎
bash "$SKILL_DIR/scripts/ol.sh" pdf "MyProject" --compiler xelatex
```

## 典型工作流

### 创建项目并开始编辑

```bash
# 1. 创建新项目
bash "$SKILL_DIR/scripts/ol.sh" create "My New Paper"

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
bash "$SKILL_DIR/scripts/ol.sh" git urls

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
bash "$SKILL_DIR/scripts/ol.sh" review list "MyProject"

# 2. 克隆项目到本地
git clone https://git@overleaf.mycompany.com/git/<project_id> /tmp/my-project

# 3. 根据 review 位置信息，在本地编辑对应文件

# 4. 推送修改
cd /tmp/my-project
git add -A
git commit -m "address review comments"
git push

# 5. 解决已处理的 review
bash "$SKILL_DIR/scripts/ol.sh" review resolve "MyProject" "<thread_id>"
```

### 编译并获取 PDF

```bash
# 1. 推送最新修改
cd /tmp/my-project
git add -A && git commit -m "final edits" && git push

# 2. 编译并下载 PDF
bash "$SKILL_DIR/scripts/ol.sh" pdf "MyProject"

# 3. 或先确认编译状态，再手动下载
bash "$SKILL_DIR/scripts/ol.sh" compile "MyProject"
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

## 代码风格偏好

扩展或修改本 skill 的脚本时，**优先拆分为多个子模块**，而非将所有逻辑堆入单一文件：

```
scripts/
  ol.sh              # 入口：环境准备 + 转发给 ol.py
  ol.py              # CLI 入口：只做命令解析与调度，不含业务逻辑
  edge_cookies.py    # 子模块：从 Edge 浏览器提取 Cookie
  api.py             # 子模块：Overleaf REST/WebSocket API 封装
  git_utils.py       # 子模块：Git URL 构造与项目列表
  review.py          # 子模块：review 线程获取与解析
  compile.py         # 子模块：编译与 PDF 下载
  ...
```

每个子模块职责单一，`ol.py` 只做 `import` 和 CLI 注册。新增功能时，新建子模块文件，不要直接往 `ol.py` 追加几百行。
