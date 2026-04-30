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
| `--mode json` | 以 JSON Lines 输出所有事件（工具调用/结果/LLM 输出）| 轨迹审计时加 |
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

## 轨迹审计（主 Agent 审计子 Agent）

使用 `--mode json` 让子 Agent 将**完整轨迹**（每步工具调用、参数、结果、LLM 输出）以 JSON Lines 输出，
供主 Agent 事后审核，判断子 Agent 是否按预期执行。

### invoke.sh `--audit <file>`（推荐）

```bash
# 轨迹写入文件，stdout 仍输出最终文本
invoke.sh --agent figure-qa \
  --audit /tmp/subagent-traj.jsonl \
  --msg $'Check image at /tmp/fig.png\nScene: academic\nIntent: pipeline diagram'
```

完成后主 Agent 用 `read` 工具读取轨迹文件，或用以下命令提取关键信息：

```bash
# 最终回答文本（通常就是 stdout 已打印的内容，此处可交叉验证）
python3 -c "
import json, sys
for line in open(sys.argv[1]):
    try:
        e = json.loads(line)
        if e.get('type')=='agent_end':
            for c in (e['messages'][-1].get('content') or []):
                if isinstance(c,dict) and c.get('type')=='text': print(c['text'])
    except: pass
" /tmp/subagent-traj.jsonl

# 所有工具调用序列（需要安装 jq）
jq -c 'select(.type=="tool_execution_start") | {tool:.toolName, args:.args}' /tmp/subagent-traj.jsonl

# 有无工具报错
jq -c 'select(.type=="tool_execution_end" and .isError==true)' /tmp/subagent-traj.jsonl

# 共几轮 LLM turn
jq 'select(.type=="turn_end")' /tmp/subagent-traj.jsonl | wc -l
```

### 手动构造（不用 invoke.sh）

```bash
pi --print \
  --model axonhub/gemini-3.1-pro-preview \
  --mode json \
  --tools read,bash \
  --system-prompt /path/to/agent.prompt.md \
  --no-skills --no-context-files --no-extensions --no-session \
  "message" > /tmp/subagent-traj.jsonl
```

### 常用 jq 查询速查

| 目的 | 命令 |
|------|------|
| 最终回答 | `jq -r 'select(.type=="agent_end") \| .messages[-1].content[] \| select(.type=="text") \| .text'` |
| 工具调用序列 | `jq -c 'select(.type=="tool_execution_start") \| {tool:.toolName,args:.args}'` |
| 工具报错 | `jq -c 'select(.type=="tool_execution_end" and .isError==true)'` |
| turn 数 | `jq 'select(.type=="turn_end")' \| wc -l` |

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

> **轨迹审计变体**：Step 2 的命令改用 `invoke.sh --audit /tmp/subagent-traj.jsonl ...`（或手动加 `--mode json > /tmp/traj.jsonl`），
> Step 4 之后额外用 `read` 工具读取 `/tmp/subagent-traj.jsonl` 获取完整轨迹。

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
