---
name: overleaf
description: 通过 pyoverleaf 与 Overleaf 项目交互。当用户需要读取、编辑、上传 LaTeX 文件，列出 Overleaf 项目，下载项目 ZIP，或在 Overleaf 编辑论文时使用。
---

# Overleaf Skill

通过 `pyoverleaf` 库与 Overleaf 实例交互，支持列出项目与文件、读写 LaTeX 文件、增量编辑文本、获取与解决 review 评论线程、下载整个项目，以及批量获取每个项目的 Git 地址。

## 环境准备

在使用任何命令前，确认以下环境变量已设置：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `OVERLEAF_HOST` | Overleaf 实例域名（不含 `https://`） | `overleaf.mycompany.com` 或 `www.overleaf.com` |
| `OVERLEAF_COOKIE` | 浏览器 Cookie 头部字符串 | `overleaf_session2=s%3Axxx; gke-route=yyy` |

获取 Cookie 的方式：在浏览器打开 Overleaf，按 F12 → Network → 任意请求 → Request Headers → Cookie 字段。

```bash
export OVERLEAF_HOST="overleaf.mycompany.com"
export OVERLEAF_COOKIE="overleaf_session2=s%3Axxx; gke-route=yyy"
```

## 调用方式

所有操作统一通过 wrapper 脚本执行：

```bash
bash scripts/ol.sh <命令> [参数]
```

## 命令参考

### 列出项目

```bash
# 列出全部项目
bash scripts/ol.sh ls

# 列出项目根目录文件
bash scripts/ol.sh ls "MyProject"

# 列出子目录
bash scripts/ol.sh ls "MyProject/chapters"
```

### 获取每个项目的 Git 地址

```bash
# 输出带缩进 JSON
bash scripts/ol.sh git urls

# 输出紧凑 JSON（便于管道处理）
bash scripts/ol.sh git urls --compact

# 覆盖默认 Git 地址前缀
bash scripts/ol.sh git urls --base-url "https://git.example.com"
```

说明：
- 默认按 `https://<OVERLEAF_HOST>/git/<project_id>` 生成 `git_url`。
- 默认按 `https://git@<OVERLEAF_HOST>/git/<project_id>` 生成 `git_clone_url`。
- 可通过 `--clone-user` 自定义克隆地址用户名（默认 `git`）。

### 读取文件

```bash
# 输出到终端
bash scripts/ol.sh read "MyProject/main.tex"

# 保存到本地
bash scripts/ol.sh read "MyProject/main.tex" > /tmp/main.tex
```

### 写入文件（覆盖）

```bash
# 从标准输入写入
echo "Hello World" | bash scripts/ol.sh write "MyProject/test.tex"

# 从本地文件写入
cat local_file.tex | bash scripts/ol.sh write "MyProject/main.tex"
```

### 增量编辑文件（edit）

```bash
# 精确匹配 old（默认必须仅匹配 1 处）
bash scripts/ol.sh edit "MyProject/main.tex" --old "\\section{Old}" --new "\\section{New}"

# 替换所有匹配
bash scripts/ol.sh edit "MyProject/main.tex" --old "\\cite{a}" --new "\\cite{b}" --replace-all
```

说明：
- `edit` 采用类似 codex/opencode 的语义：`old` 必须精确匹配（包含空格和换行）。
- 默认要求唯一匹配。若匹配到 0 处或多处会报错。
- 加 `--replace-all` 后会替换全部匹配。

### 创建目录

```bash
bash scripts/ol.sh mkdir "MyProject/figures"
bash scripts/ol.sh mkdir -p "MyProject/sections/appendix"
```

### 删除文件或目录

```bash
bash scripts/ol.sh rm "MyProject/old_draft.tex"
```

### 获取项目 review 评论线程

```bash
# 输出带缩进 JSON
bash scripts/ol.sh review list "MyProject"

# 输出紧凑 JSON（便于管道处理）
bash scripts/ol.sh review list "MyProject" --compact
```

### 自动定位某条 review 对应文件

```bash
# 输出单条线程的精确 doc/path 映射（基于 Overleaf doc comments）
bash scripts/ol.sh review locate "MyProject" "69c2745dc0f84b044e000001"
```

说明：
- `review list` 默认已经包含每条 review 的 `location` 字段（`doc_id`、`path`、`line`、`position`）。
- 定位基于 Overleaf 的 `joinDoc` 原生 comments 数据，不使用关键词猜测。

### 标记 review 线程为已解决

```bash
# 使用线程首条消息用户作为 resolve 用户
bash scripts/ol.sh review resolve "MyProject" "69c2745dc0f84b044e000001"

# 显式指定 user_id
bash scripts/ol.sh review resolve "MyProject" "69c2745dc0f84b044e000001" --user-id "69a65a7a8f69a4e6b57d0ddd"
```

### 下载整个项目

```bash
bash scripts/ol.sh download "MyProject" /tmp/MyProject.zip
```

## 安全规则（重要）

这些规则不是强制约束，而是说明为什么要这样做：Overleaf 的写操作直接修改云端文件，误操作会影响所有协作者，且无法在本地撤销。

**执行任何写操作前（write、mkdir、rm），必须：**

1. **先读取**当前版本（`read` 命令）
2. **展示差异**，让用户确认即将发生的变更
3. **等待用户明确授权**（"确认写入"、"yes"等明确意思的回复）
4. **仅执行一次**写操作，不批量推送

**以下情况中止操作并告知用户：**
- `OVERLEAF_COOKIE` 未设置或已过期（HTTP 401/403）
- 项目不存在或无权限
- 文件路径格式错误

## 典型工作流

### 读取并编辑文件

```bash
# 1. 查看项目结构
bash scripts/ol.sh ls "MyProject"

# 2. 读取目标文件
bash scripts/ol.sh read "MyProject/main.tex" > /tmp/main.tex

# 3. 在本地编辑（由 agent 或用户完成）

# 4. 向用户展示 diff，等待确认
diff /tmp/main.tex /tmp/main_edited.tex

# 5. 用户确认后写回
cat /tmp/main_edited.tex | bash scripts/ol.sh write "MyProject/main.tex"
```

### 下载项目用于本地编译

```bash
bash scripts/ol.sh download "MyProject" ~/Downloads/MyProject.zip
unzip ~/Downloads/MyProject.zip -d ~/Downloads/MyProject
```

## 已知限制

- `pyoverleaf` 的 Cookie 认证依赖浏览器登录状态，Cookie 过期后需重新获取
- 不支持创建新项目（需在 Overleaf 界面完成）
- WebSocket 操作（读取 `.tex` doc 类型文件）在网络不稳定时可能超时，可重试
- `review list/review locate/review resolve` 依赖 Overleaf 的内部评论线程与 `joinDoc` 接口（非官方公开 API）；不同私有部署版本可能存在字段差异
- `git urls` 依赖 `GET /user/projects` 接口返回项目列表；若实例关闭该接口或 Cookie 无权限，会返回 401/403
- 当前 Overleaf 实例（`OVERLEAF_HOST`）未通网时，所有命令均失败，这是预期行为

## 依赖

- `pyoverleaf`：通过 `uv tool install pyoverleaf` 安装
- Python 解释器路径：`~/.local/share/uv/tools/pyoverleaf/bin/python`
