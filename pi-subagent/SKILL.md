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

子 Agent 运行后，完整轨迹（每步工具调用、参数、结果、LLM 输出）自动保存到
`/tmp/pi-subagent-<name>-last.jsonl`，主 Agent 随时可读取审计。

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
| `--mode json` | 以 JSON Lines 输出所有事件（工具调用/结果/LLM 输出）| 必须加，轨迹来源 |
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
所有模板均以 `--mode json` 运行，将轨迹重定向到文件，从中提取最终文本输出。

### 场景 A：有预定义 system prompt，完全隔离
适合 figure-qa 等无需外部 skill 的审查 agent。
推荐模型：`axonhub/gemini-3.1-pro-preview`（视觉理解）

```bash
TRAJ=/tmp/pi-subagent-myagent-last.jsonl
pi --print \
  --model axonhub/gemini-3.1-pro-preview \
  --thinking off \
  --tools read,bash \
  --mode json \
  --system-prompt /path/to/agent.prompt.md \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  "your message" > "$TRAJ"
# 从轨迹提取最终文本
python3 -c "
import json,sys
for l in open(sys.argv[1]):
    e=json.loads(l)
    if e.get('type')=='agent_end':
        for c in e['messages'][-1].get('content',[]):
            if c.get('type')=='text': print(c['text'])
" "$TRAJ"
```

### 场景 B：需要加载某个 skill

```bash
TRAJ=/tmp/pi-subagent-myagent-last.jsonl
pi --print \
  --model axonhub/claude-opus-4-7 \
  --thinking off \
  --tools read,bash \
  --mode json \
  --skill /path/to/skill \
  --no-skills \
  --no-context-files \
  --no-session \
  "your message" > "$TRAJ"
```

### 场景 C：快速单次推理，无工具，低成本

```bash
TRAJ=/tmp/pi-subagent-myagent-last.jsonl
pi --print \
  --model axonhub/gemini-3-flash-preview \
  --mode json \
  --no-tools \
  --no-skills \
  --no-context-files \
  --no-session \
  "your message" > "$TRAJ"
```

### 场景 D：需要深度推理

```bash
TRAJ=/tmp/pi-subagent-myagent-last.jsonl
pi --print \
  --model axonhub/gemini-3.1-pro-preview \
  --thinking high \
  --tools read,bash \
  --mode json \
  --no-skills \
  --no-context-files \
  --no-session \
  "your message" > "$TRAJ"
```

---

## herdr 五步流程

> **规则：`pane_split` 时必须传 `newPane` 起别名。**
> 后续所有 `run` / `wait_agent` / `read` / `watch` / `send` / `stop` 均通过别名引用，不得使用数字 pane id。

**Step 1 — 创建 pane 并命名别名**

```json
{ "action": "pane_split", "direction": "down", "newPane": "subagent" }
```

**Step 2 — 启动 sub-agent**

```json
{
  "action": "run",
  "pane": "subagent",
  "command": "<根据上方模板构造的 pi --print 命令，重定向到 /tmp/pi-subagent-<name>-last.jsonl>"
}
```

**Step 3 — 等待完成**

```json
{ "action": "wait_agent", "pane": "subagent", "statuses": ["done", "idle"], "timeout": 120000 }
```

**Step 4 — 读取最终文本**（从轨迹文件提取）

```json
{
  "action": "run",
  "pane": "subagent",
  "command": "python3 -c \"import json,sys\nfor l in open(sys.argv[1]):\n    e=json.loads(l)\n    if e.get('type')=='agent_end':\n        for c in e['messages'][-1].get('content',[]):\n            if c.get('type')=='text': print(c['text'])\n\" /tmp/pi-subagent-<name>-last.jsonl"
}
```

**Step 5 — 读取完整轨迹**（主 Agent 审计）

用 `read` 工具直接读取轨迹文件：
```
/tmp/pi-subagent-<name>-last.jsonl
```

或用 jq 过滤所需事件：

```bash
# 工具调用序列
jq -c 'select(.type=="tool_execution_start") | {tool:.toolName, args:.args}' /tmp/pi-subagent-<name>-last.jsonl

# 工具报错
jq -c 'select(.type=="tool_execution_end" and .isError==true)' /tmp/pi-subagent-<name>-last.jsonl

# turn 数
jq 'select(.type=="turn_end")' /tmp/pi-subagent-<name>-last.jsonl | wc -l
```

---

## invoke.sh（便捷调用器）

`scripts/invoke.sh` 封装了上述流程：读取 `agents/<name>.md` frontmatter，自动组装 `--mode json` 命令，
将轨迹写入 `/tmp/pi-subagent-<name>-last.jsonl`，同时将最终文本打印到 stdout。

```bash
invoke.sh --agent <name> [--model <model_string>] --msg '<message>' [-- <extra_pi_flags>]
```

```bash
# 示例
invoke.sh --agent figure-qa \
  --msg $'Check image at /tmp/fig.png\nScene: academic\nIntent: pipeline diagram'

# 完成后轨迹已在 /tmp/pi-subagent-figure-qa-last.jsonl，主 Agent 直接 read 即可
```

`--` 之后的参数透传给 pi（如 `-- --thinking medium`）。

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

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件 |
| `agents/<name>.md` | 调用文档 + frontmatter 默认值 |
| `agents/<name>.prompt.md` | System prompt 正文 |
| `scripts/invoke.sh` | 便捷调用器 |

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 模型名不对 | 模型已更新 | `pi --list-models` 查最新列表 |
| pane 一直不变 `done` | pi 报错 | `herdr read --source recent-unwrapped` 查看错误 |
| 轨迹文件为空 | stdout 重定向失败 | 检查命令末尾是否有 `> /tmp/...` |
| 需要 `--skill` 但担心冲突 | `--no-skills` 禁用自动发现，`--skill` 显式路径仍生效 | 两者可以同时用 |
