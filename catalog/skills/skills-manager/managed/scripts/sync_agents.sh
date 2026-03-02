#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"

TARGET_AGENT="${1:-all}"

echo "sync_agents.sh"
echo "repo_root=${REPO_ROOT}"
echo "target_agent=${TARGET_AGENT}"
echo "status=placeholder"
