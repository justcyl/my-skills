---
name: pi-subagent
description: >
  在 herdr pane 中用 pi --print 调度 sub-agent 的基础设施。
  提供 agent 定义规范（frontmatter + system prompt）和通用调用模板。
  调用前请先读懂 pi 参数含义，根据具体场景构造合适的命令，而非直接套用脚本。
  触发语境："spawn a sub-agent""调用子代理""pi --print""figure-qa""视觉审查"。
---

# Pi Sub-Agent Infrastructure

在 herdr pane 中用 `pi --print` 运行 sub-agent。

**查看可用模型（唯一事实来源）：**
```bash
pi --list-models
```

---

## Pi 参数速查

调用前必须理解每个参数的作用，根据场景选用，不要盲目套模板：

| 参数 | 作用 | 常用值 |
|------|------|--------|
| `--print` | 非交互模式，处理完即退出 | 必须加 |
| `--model` | 指定模型 | `axonhub/gemini-3.1-pro-preview`（视觉/推理）<br>`axonhub/gemini-3-flash-preview`（快速/低成本）<br>`axonhub/claude-opus-4-7`（代码/长文本）|
| `--thinking` | 推理深度 | `off`（默认）/ `low` / `medium` / `high` / `xhigh` |
| `--tools` | 允许的工具白名单 | `read,bash`（常用）/ `read`（只读）/ 不传则全部可用 |
| `--system-prompt` | system prompt，可传文字或文件路径 | `"You are ..."` 或 `/path/to/prompt.md` |
| `--skill` | 加载指定 skill 文件/目录 | `/path/to/skill` |
| `--no-skills` | 禁用 skill 自动发现（`--skill` 显式路径仍生效）| 隔离 agent 时加 |
| `--no-context-files` | 禁用 AGENTS.md / CLAUDE.md 自动加载 | 隔离 agent 时加 |
| `--no-extensions` | 禁用扩展自动发现 | 隔离 agent 时加 |
| `--no-session` | 不保存会话文件 | 临时 agent 加 |
| `--append-system-prompt` | 追加内容到 system prompt | 可多次使用 |

---

## 参考调用模板

以下是常见场景的参考命令。**在实际调用前，请先确认每个参数是否适合你的场景，按需增删。**

### 场景 A：有预定义 system prompt，完全隔离
适合 figure-qa 等无需外部 skill 的审查 agent。
推荐模型：`axonhub/gemini-3.1-pro-preview`（视觉理解）

```bash
pi --print \
  --model axonhub/gemini-3.1-pro-preview \
  --thinking off \
  --tools read,bash \
  --system-prompt /path/to/agent.prompt.md \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  "your message"
```

### 场景 B：需要加载某个 skill
`--no-skills` 禁用自动发现，`--skill` 显式加载仍然生效。
推荐模型：根据 skill 能力选择（代码/分析用 `axonhub/claude-opus-4-7`，视觉用 gemini）

```bash
pi --print \
  --model axonhub/claude-opus-4-7 \
  --thinking off \
  --tools read,bash \
  --skill /path/to/skill \
  --no-skills \
  --no-context-files \
  --no-session \
  "your message"
```

### 场景 C：快速单次推理，无工具，低成本
推荐模型：`axonhub/gemini-3-flash-preview`

```bash
pi --print \
  --model axonhub/gemini-3-flash-preview \
  --no-tools \
  --no-skills \
  --no-context-files \
  --no-session \
  "your message"
```

### 场景 D：需要深度推理
推荐模型：`axonhub/gemini-3.1-pro-preview` + `--thinking high`
或 `axonhub/claude-opus-4-7` + `--thinking high`

```bash
pi --print \
  --model axonhub/gemini-3.1-pro-preview \
  --thinking high \
  --tools read,bash \
  --no-skills \
  --no-context-files \
  --no-session \
  "your message"
```

---

## herdr 四步流程

```json
{ "action": "pane_split", "direction": "down", "newPane": "subagent" }
```

```json
{
  "action": "run",
  "pane": "subagent",
  "command": "<根据上方模板构造的 pi --print 命令>"
}
```

```json
{ "action": "wait_agent", "pane": "subagent", "statuses": ["done", "idle"], "timeout": 120000 }
```

```json
{ "action": "read", "pane": "subagent", "source": "recent-unwrapped", "lines": 100 }
```

---

## Agent 定义格式

`agents/<name>.md` — frontmatter（默认参数）+ 调用文档：

```markdown
---
name: <agent-name>
description: 一句话说明
model: axonhub/gemini-3.1-pro-preview   # pi --list-models 中的完整字符串
thinking: off                            # off / minimal / low / medium / high / xhigh
tools: read,bash
---

# 调用方式 / 输入格式 / 输出格式 / 结果处理
```

`agents/<name>.prompt.md` — 纯 system prompt 正文，无 frontmatter。

---

## Agent 目录

| agent | 文件 | 功能 |
|-------|------|------|
| `figure-qa` | `agents/figure-qa.md` | AI 生成图片视觉 QA，输出结构化 Figure QA Report |

---

## invoke.sh（参考实现，非推荐路径）

`scripts/invoke.sh` 是一个便捷包装：读取 `agents/<name>.md` 的 frontmatter，自动组装 pi 命令。
适合快速调用预定义 agent，但**隐藏了具体参数**——调用前请先读懂 `agents/<name>.md` 中的说明，确认参数合适再使用。

```bash
invoke.sh --agent <name> [--model <model_string>] --msg '<message>' [-- <extra_pi_flags>]
```

`--` 之后的参数透传给 pi（如 `-- --thinking medium`）。

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件 |
| `agents/<name>.md` | 调用文档 + frontmatter 默认值 |
| `agents/<name>.prompt.md` | System prompt 正文 |
| `scripts/invoke.sh` | 便捷调用器（参考实现） |

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 模型名不对 | 模型已更新 | `pi --list-models` 查最新列表 |
| pane 一直不变 `done` | pi 报错 | `herdr read --source recent-unwrapped` 查看错误 |
| 需要 `--skill` 但担心冲突 | `--no-skills` 禁用自动发现，`--skill` 显式路径仍生效 | 两者可以同时用 |
