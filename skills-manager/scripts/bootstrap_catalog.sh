#!/usr/bin/env bash
set -euo pipefail

# 解析当前脚本所在 skill 的根目录，再回到仓库根目录。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"

echo "bootstrap_catalog.sh"
echo "repo_root=${REPO_ROOT}"
echo "status=placeholder"
echo "next=bootstrap existing skills into catalog"
