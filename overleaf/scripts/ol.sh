#!/usr/bin/env bash
# ol.sh — Overleaf CLI 入口脚本
# 使用 pyoverleaf uv tool 内置的 Python 解释器运行 ol.py，
# 确保 pyoverleaf 包可被正确导入。

set -euo pipefail

PYOVERLEAF_PYTHON="${HOME}/.local/share/uv/tools/pyoverleaf/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$PYOVERLEAF_PYTHON" ]]; then
    echo "错误：未找到 pyoverleaf 的 Python 解释器：$PYOVERLEAF_PYTHON" >&2
    echo "请先执行：uv tool install pyoverleaf" >&2
    exit 1
fi

exec "$PYOVERLEAF_PYTHON" "$SCRIPT_DIR/ol.py" "$@"
