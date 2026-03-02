#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"

SOURCE="${1:-}"

if [[ -z "${SOURCE}" ]]; then
  echo "usage: bash skills-manager/scripts/import_skill.sh <source>" >&2
  exit 1
fi

echo "import_skill.sh"
echo "repo_root=${REPO_ROOT}"
echo "source=${SOURCE}"
echo "status=placeholder"
