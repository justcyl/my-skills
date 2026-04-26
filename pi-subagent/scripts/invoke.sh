#!/usr/bin/env bash
# invoke.sh — 通用 pi sub-agent 调用器
#
# 用法：
#   invoke.sh --agent <name> [--model <alias>] --msg '<message>'
#
# 参数：
#   --agent  <name>    必填，对应 agents/<name>.md
#   --model  <alias>   可选，覆盖 agent frontmatter 中的 model 字段
#   --msg    <text>    必填，传给 sub-agent 的用户消息
#
# 示例：
#   invoke.sh --agent figure-qa --msg "Check image at /tmp/fig.png\nScene: academic\nIntent: Pipeline overview"
#   invoke.sh --agent figure-qa --model gemini-flash --msg "Quick check: /tmp/test.png"

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/models.sh
source "$SKILL_DIR/scripts/models.sh"

AGENT=""
MODEL_ALIAS=""
MSG=""

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --agent) AGENT="${2:?--agent requires a value}"; shift 2 ;;
    --model) MODEL_ALIAS="${2:?--model requires a value}"; shift 2 ;;
    --msg)   MSG="${2:?--msg requires a value}"; shift 2 ;;
    -h|--help)
      echo "Usage: invoke.sh --agent <name> [--model <alias>] --msg '<message>'"
      echo ""
      echo "Options:"
      echo "  --agent  <name>   Required. Agent name, maps to agents/<name>.md"
      echo "  --model  <alias>  Optional. Model alias from routing.md (overrides agent default)"
      echo "  --msg    <text>   Required. User message for the sub-agent (\\n for newlines)"
      exit 0
      ;;
    *)
      echo "invoke.sh: unknown argument '$1'" >&2
      echo "Usage: invoke.sh --agent <name> [--model <alias>] --msg '<message>'" >&2
      exit 1
      ;;
  esac
done

# Validate required args
if [[ -z "$AGENT" ]]; then
  echo "invoke.sh: --agent is required" >&2
  exit 1
fi
if [[ -z "$MSG" ]]; then
  echo "invoke.sh: --msg is required" >&2
  exit 1
fi

# Locate agent contract file (frontmatter + caller docs)
AGENT_FILE="$SKILL_DIR/agents/${AGENT}.md"
if [[ ! -f "$AGENT_FILE" ]]; then
  echo "invoke.sh: agent not found: $AGENT_FILE" >&2
  echo "Available agents:" >&2
  ls "$SKILL_DIR/agents/"*.md 2>/dev/null | grep -v '\.prompt\.md$' | sed "s|$SKILL_DIR/agents/||;s|\.md$||" >&2 || echo "  (none)" >&2
  exit 1
fi

# Locate system prompt file (<agent>.prompt.md)
PROMPT_FILE="$SKILL_DIR/agents/${AGENT}.prompt.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "invoke.sh: system prompt not found: $PROMPT_FILE" >&2
  exit 1
fi

# Extract default model alias from frontmatter (line: "model: <alias>")
if [[ -z "$MODEL_ALIAS" ]]; then
  MODEL_ALIAS=$(awk '/^---/{f++; next} f==1 && /^model:/{print $2; exit}' "$AGENT_FILE")
  MODEL_ALIAS="${MODEL_ALIAS:-gemini-pro}"
fi

# Extract tools override from frontmatter (line: "tools: <list>")
FRONTMATTER_TOOLS=$(awk '/^---/{f++; next} f==1 && /^tools:/{print $2; exit}' "$AGENT_FILE")

# Resolve model alias → model_string thinking tools
read -r MODEL_STR THINKING TOOLS <<< "$(resolve_model "$MODEL_ALIAS")"

# Frontmatter tools override (if present, takes precedence over model default)
if [[ -n "$FRONTMATTER_TOOLS" ]]; then
  TOOLS="$FRONTMATTER_TOOLS"
fi

# Read system prompt directly from .prompt.md (no parsing needed)
SYSTEM_PROMPT=$(cat "$PROMPT_FILE")

# Expand \n in message to real newlines
MSG="$(printf '%b' "$MSG")"

# Run the sub-agent
exec pi --print \
  --model "$MODEL_STR" \
  --thinking "$THINKING" \
  --tools "$TOOLS" \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  --system-prompt "$SYSTEM_PROMPT" \
  "$MSG"
