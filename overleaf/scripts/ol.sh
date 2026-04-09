#!/usr/bin/env bash
# ol.sh — Overleaf CLI 入口脚本
# 使用 pyoverleaf uv tool 内置的 Python 解释器运行 ol.py，
# 确保 pyoverleaf 包可被正确导入。

set -euo pipefail

PYOVERLEAF_PYTHON="${HOME}/.local/share/uv/tools/pyoverleaf/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 若未设置 OVERLEAF_COOKIE，自动从 Edge 浏览器提取
if [[ -z "${OVERLEAF_COOKIE:-}" ]]; then
    OVERLEAF_HOST="${OVERLEAF_HOST:-www.overleaf.com}"
    OVERLEAF_HOST="${OVERLEAF_HOST#https://}"
    OVERLEAF_HOST="${OVERLEAF_HOST#http://}"
    OVERLEAF_HOST="${OVERLEAF_HOST%/}"
    if OVERLEAF_COOKIE=$("$PYOVERLEAF_PYTHON" "$SCRIPT_DIR/edge_cookies.py" "$OVERLEAF_HOST" 2>/dev/null); then
        export OVERLEAF_COOKIE
    else
        echo "警告：无法从 Edge 浏览器自动获取 Cookie，请手动设置 OVERLEAF_COOKIE" >&2
    fi
fi

if [[ ! -x "$PYOVERLEAF_PYTHON" ]]; then
    echo "错误：未找到 pyoverleaf 的 Python 解释器：$PYOVERLEAF_PYTHON" >&2
    echo "请先执行：uv tool install pyoverleaf" >&2
    exit 1
fi

exec "$PYOVERLEAF_PYTHON" "$SCRIPT_DIR/ol.py" "$@"
