#!/usr/bin/env bash
# ol.sh — Overleaf CLI 入口脚本
# 使用 pyoverleaf uv tool 内置的 Python 解释器运行 ol.py，
# 确保 pyoverleaf 包可被正确导入。

set -euo pipefail

PYOVERLEAF_PYTHON="${HOME}/.local/share/uv/tools/pyoverleaf/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${XDG_CONFIG_HOME:-${HOME}/.config}/overleaf/config.env"

# Load optional local configuration. Keep this file user-owned and mode 600.
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$CONFIG_FILE"
    set +a
fi

if [[ ! -x "$PYOVERLEAF_PYTHON" ]]; then
    echo "错误：未找到 pyoverleaf 的 Python 解释器：$PYOVERLEAF_PYTHON" >&2
    echo "请先执行：uv tool install pyoverleaf" >&2
    exit 1
fi

# 若未设置 OVERLEAF_COOKIE，优先使用 WSL 内的账号密码登录。
if [[ -z "${OVERLEAF_COOKIE:-}" ]]; then
    OVERLEAF_HOST="${OVERLEAF_HOST:-www.overleaf.com}"
    OVERLEAF_HOST="${OVERLEAF_HOST#https://}"
    OVERLEAF_HOST="${OVERLEAF_HOST#http://}"
    OVERLEAF_HOST="${OVERLEAF_HOST%/}"
    export OVERLEAF_HOST
    if [[ -n "${OVERLEAF_EMAIL:-}" || -n "${OVERLEAF_PASSWORD_FILE:-}" || -n "${OVERLEAF_PASSWORD_COMMAND:-}" ]]; then
        OVERLEAF_COOKIE=$("$PYOVERLEAF_PYTHON" "$SCRIPT_DIR/auth.py")
        export OVERLEAF_COOKIE
    else
        # macOS fallback for the original browser-cookie workflow.
        if OVERLEAF_COOKIE=$("$PYOVERLEAF_PYTHON" "$SCRIPT_DIR/edge_cookies.py" "$OVERLEAF_HOST" 2>/dev/null); then
            export OVERLEAF_COOKIE
        else
            echo "错误：未配置 WSL 登录凭据，也无法从 Edge 浏览器自动获取 Cookie。" >&2
            echo "请设置 OVERLEAF_EMAIL + OVERLEAF_PASSWORD_FILE/OVERLEAF_PASSWORD_COMMAND。" >&2
            exit 1
        fi
    fi
fi

exec "$PYOVERLEAF_PYTHON" "$SCRIPT_DIR/ol.py" "$@"
