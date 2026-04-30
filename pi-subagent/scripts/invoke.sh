#!/usr/bin/env bash
# invoke.sh — pi sub-agent 调用器
#
# 用法：
#   invoke.sh --agent <name> [--model <model>] --msg '<message>' [-- <extra_pi_flags...>]
#
# 参数：
#   --agent  <name>    必填，对应 agents/<name>.md
#   --model  <model>   可选，直接传模型字符串（如 axonhub/gemini-3.1-pro-preview），覆盖 frontmatter
#   --msg    <text>    必填，传给 sub-agent 的用户消息（支持 \n 换行）
#   -- <flags>         可选，追加到 pi 命令末尾的额外标志
#
# 行为：
#   始终以 --mode json 运行，将完整轨迹（工具调用/结果/LLM 输出）写入
#   /tmp/pi-subagent-<name>-last.jsonl，供主 Agent 事后读取审计。
#   stdout 输出最终文本回答（从 JSON 轨迹中提取）。
#
# 查看可用模型：pi --list-models
#
# 示例：
#   invoke.sh --agent figure-qa --msg "Check image at /tmp/fig.png\nScene: academic"
#
#   # 覆盖模型
#   invoke.sh --agent figure-qa --model axonhub/gemini-3-flash-preview --msg "Quick check"
#
#   # 追加额外 pi 标志（如加深度推理）
#   invoke.sh --agent figure-qa --msg "..." -- --thinking medium

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

AGENT=""
MODEL_OVERRIDE=""
MSG=""
EXTRA_FLAGS=()

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --agent) AGENT="${2:?--agent requires a value}"; shift 2 ;;
    --model) MODEL_OVERRIDE="${2:?--model requires a value}"; shift 2 ;;
    --msg)   MSG="${2:?--msg requires a value}"; shift 2 ;;
    --) shift; EXTRA_FLAGS=("$@"); break ;;
    -h|--help)
      grep '^#' "${BASH_SOURCE[0]}" | head -25 | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "invoke.sh: unknown argument '$1'" >&2
      echo "Usage: invoke.sh --agent <name> [--model <model>] --msg '<message>' [-- <extra_pi_flags>]" >&2
      exit 1
      ;;
  esac
done

# Validate
[[ -z "$AGENT" ]] && { echo "invoke.sh: --agent is required" >&2; exit 1; }
[[ -z "$MSG" ]]   && { echo "invoke.sh: --msg is required" >&2; exit 1; }

# Locate files
AGENT_FILE="$SKILL_DIR/agents/${AGENT}.md"
PROMPT_FILE="$SKILL_DIR/agents/${AGENT}.prompt.md"

if [[ ! -f "$AGENT_FILE" ]]; then
  echo "invoke.sh: agent not found: $AGENT_FILE" >&2
  echo "Available agents:" >&2
  ls "$SKILL_DIR/agents/"*.md 2>/dev/null \
    | grep -v '\.prompt\.md$' \
    | sed "s|$SKILL_DIR/agents/||;s|\.md$||" >&2 \
    || echo "  (none)" >&2
  exit 1
fi

[[ ! -f "$PROMPT_FILE" ]] && { echo "invoke.sh: system prompt not found: $PROMPT_FILE" >&2; exit 1; }

# Read a field from YAML frontmatter (between first pair of ---)
read_frontmatter() {
  local key="$1" file="$2"
  awk '/^---/{f++; next} f==1 && /^'"$key"':/{$1=""; sub(/^ /, ""); print; exit}' "$file"
}

# Resolve model: CLI > frontmatter > default
MODEL="${MODEL_OVERRIDE:-$(read_frontmatter model "$AGENT_FILE")}"
MODEL="${MODEL:-axonhub/gemini-3.1-pro-preview}"

THINKING="$(read_frontmatter thinking "$AGENT_FILE")"
THINKING="${THINKING:-off}"

TOOLS="$(read_frontmatter tools "$AGENT_FILE")"
TOOLS="${TOOLS:-read,bash}"

# Trajectory file: always written, main agent can read it after completion
TRAJ_FILE="/tmp/pi-subagent-${AGENT}-last.jsonl"

# Expand \n in message to real newlines
MSG="$(printf '%b' "$MSG")"

# Run with --mode json, save trajectory, extract final text to stdout
pi --print \
  --model "$MODEL" \
  --thinking "$THINKING" \
  --tools "$TOOLS" \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  --mode json \
  --system-prompt "$(cat "$PROMPT_FILE")" \
  "${EXTRA_FLAGS[@]}" \
  "$MSG" > "$TRAJ_FILE"

# Extract and print final text answer from trajectory
python3 - "$TRAJ_FILE" <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    line = line.strip()
    if not line:
        continue
    try:
        e = json.loads(line)
        if e.get('type') == 'agent_end':
            msgs = e.get('messages', [])
            if msgs:
                for c in (msgs[-1].get('content') or []):
                    if isinstance(c, dict) and c.get('type') == 'text':
                        print(c['text'])
    except Exception:
        pass
EOF
