#!/usr/bin/env bash
# models.sh — 模型路由解析函数
#
# 用法：source 本文件后调用 resolve_model <alias>
# 输出：三列，空格分隔："<model_string> <thinking> <tools>"
#
# 例：
#   source scripts/models.sh
#   read -r MODEL THINKING TOOLS <<< "$(resolve_model gemini-pro)"
#   # MODEL=axonhub/gemini-3.1-pro-preview  THINKING=off  TOOLS=read,bash

resolve_model() {
  local alias="${1:-gemini-pro}"
  case "$alias" in
    gemini-pro)    echo "axonhub/gemini-3.1-pro-preview off read,bash" ;;
    gemini-flash)  echo "axonhub/gemini-3.1-flash-preview off read,bash" ;;
    gemini-think)  echo "axonhub/gemini-3.1-pro-preview on read,bash" ;;
    claude-sonnet) echo "anthropic/claude-sonnet-4-5 off read,bash" ;;
    claude-think)  echo "anthropic/claude-opus-4 on read,bash" ;;
    *)
      echo "pi-subagent/models.sh: unknown alias '$alias', falling back to gemini-pro" >&2
      echo "axonhub/gemini-3.1-pro-preview off read,bash"
      ;;
  esac
}
