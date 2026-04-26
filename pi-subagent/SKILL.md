---
name: pi-subagent
description: 通用 pi sub-agent 基础设施。把 pi + herdr 创建 sub-agent 的模式抽象为可复用组件：模型路由表（alias → 实际模型 + 参数）、agent 目录（每种能力一个 system prompt md）、通用 invoke.sh。其他 skill 或 agent 直接引用 invoke.sh 和 agent 目录来调度 sub-agent，无需为每种能力单独维护一套 invoke 脚本。触发场景：'创建 sub-agent'、'用 pi 跑个子任务'、'需要调用 gemini 做 X'、'spawn a sub-agent'。
---

# Pi Sub-Agent Infrastructure

本 skill 提供在 herdr 中用 `pi --print` 调度 sub-agent 的完整基础设施：

- **模型路由** — `routing.md` + `scripts/models.sh`：alias 映射到实际模型字符串和 flag
- **Agent 目录** — `agents/*.md`：每个文件是一种能力的 YAML frontmatter + system prompt
- **通用调用器** — `scripts/invoke.sh`：读 agent 文件 + 解析模型，组装并运行 `pi --print`

其他 skill 要 spawn sub-agent，只需引用这里的 `invoke.sh` 和 `agents/` 目录，无需复制 invoke 逻辑。

---

## Quick Start

在 herdr 中 spawn 一个 sub-agent，分四步：

### Step 1 — Split 新 pane

```json
{
  "action": "pane_split",
  "direction": "down",
  "newPane": "subagent"
}
```

### Step 2 — Run sub-agent

```json
{
  "action": "run",
  "pane": "subagent",
  "command": "bash ~/.agents/skills/pi-subagent/scripts/invoke.sh --agent <agent-name> --msg '<user message>'"
}
```

可选：用 `--model <alias>` 覆盖 agent 默认模型：

```json
{
  "action": "run",
  "pane": "subagent",
  "command": "bash ~/.agents/skills/pi-subagent/scripts/invoke.sh --agent figure-qa --model gemini-pro --msg 'Check image at /tmp/fig.png\nScene: academic\nIntent: Pipeline overview'"
}
```

### Step 3 — 等待完成

```json
{
  "action": "wait_agent",
  "pane": "subagent",
  "statuses": ["done", "idle"],
  "timeout": 120000
}
```

### Step 4 — 读取输出

```json
{
  "action": "read",
  "pane": "subagent",
  "source": "recent-unwrapped",
  "lines": 100
}
```

---

## 模型路由

查看 `routing.md` 获取所有可用 alias 及对应模型字符串。

常用 alias：

| alias | 适用场景 |
|-------|---------|
| `gemini-pro` | 视觉理解、综合推理（默认）|
| `gemini-flash` | 快速、低成本任务 |
| `gemini-think` | 需要深度推理的任务 |
| `claude-sonnet` | 代码生成、长文本理解 |
| `claude-think` | 复杂规划、多步推理 |

---

## Agent 目录

`agents/` 目录下每个 `.md` 是一种 sub-agent 能力：

| 文件 | 用途 |
|------|------|
| `agents/figure-qa.md` | AI 生成图片的视觉 QA |

查看 `routing.md` 获取完整列表和各 agent 的默认模型。

---

## 扩展指南

### 添加新 Agent 类型

在 `agents/` 下新建两个文件：

**`agents/<name>.md`** — Caller Contract（其他 skill 引用这个文件了解如何使用）：

```markdown
---
name: <agent-name>
description: 一句话说明这个 agent 做什么
model: <alias>          # 来自 routing.md 的模型 alias
tools: read,bash        # pi 工具列表，逗号分隔，无空格
---

# <agent-name> Agent

## 调用方式
...

## 输入格式
...

## 输出格式
...

## 结果处理
...
```

**`agents/<name>.prompt.md`** — 纯 system prompt（直接传给 `pi --system-prompt`，无需解析）：

```
You are a <role>...
[system prompt body, no frontmatter]
```

然后用 `invoke.sh --agent <name>` 调用即可。

### 添加/修改模型路由

编辑 `routing.md`（文档）和 `scripts/models.sh`（机器可读）中的对应条目，保持两者同步。

---

## 在其他 Skill 中引用

如果你的 skill 需要 spawn sub-agent，在 `invoke.sh` 中直接调用：

```bash
bash ~/.agents/skills/pi-subagent/scripts/invoke.sh \
  --agent figure-qa \
  --msg "Check the image at: $IMAGE_PATH\nScene: $SCENE\nIntent: $INTENT"
```

不需要在你的 skill 里维护 `pi --print` 调用逻辑。

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `invoke.sh: No such file` | skill 未分发 | 运行 `distribute_skills.sh` |
| `Agent not found` | `agents/<name>.md` 不存在 | 检查 agent 文件名，或新建 agent |
| `Unknown model alias` | alias 不在 `models.sh` 中 | 查看 `routing.md` 或扩展 `models.sh` |
| pane 一直不变 `done` | pi 报错或模型不可用 | `herdr read --source recent-unwrapped` 查看错误 |

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件，主入口 |
| `routing.md` | 模型路由表 + agent 目录（人可读）|
| `agents/<name>.md` | Caller Contract：调用方式、输入格式、输出格式、结果处理 |
| `agents/<name>.prompt.md` | System prompt 正文（直接传给 `pi --system-prompt`）|
| `scripts/models.sh` | bash 可 source 的模型解析函数 |
| `scripts/invoke.sh` | 通用 sub-agent 调用器 |
