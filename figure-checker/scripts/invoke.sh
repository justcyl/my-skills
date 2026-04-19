#!/usr/bin/env bash
# Usage: invoke.sh <image_path> <scene> <intent> [extra_context]
#
# Spawns a figure-checker sub-agent using pi --print and prints the QA report.
# Called by the figure-checker skill via herdr.

set -euo pipefail

IMAGE_PATH="${1:?Usage: invoke.sh <image_path> <scene> <intent> [extra_context]}"
SCENE="${2:-general}"
INTENT="${3:?Intent is required}"
EXTRA="${4:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/prompt.md"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: prompt.md not found at $PROMPT_FILE" >&2
  exit 1
fi

if [[ ! -f "$IMAGE_PATH" ]]; then
  echo "ERROR: Image not found at $IMAGE_PATH" >&2
  exit 1
fi

# Build the user message
USER_MSG="Check the image at: $IMAGE_PATH
Scene: $SCENE
Intent: $INTENT"

if [[ -n "$EXTRA" ]]; then
  USER_MSG="$USER_MSG
$EXTRA"
fi

# Run the figure-checker sub-agent
# --system-prompt: replaces default coding-assistant prompt with figure-checker instructions
# --no-skills/--no-context-files/--no-extensions: isolate the sub-agent from host environment
exec pi --print \
  --model "axonhub/gemini-3.1-pro-preview" \
  --thinking off \
  --tools "read,bash" \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  --system-prompt "$(cat "$PROMPT_FILE")" \
  "$USER_MSG"
