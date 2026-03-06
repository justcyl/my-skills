#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

usage() {
  cat >&2 <<'TEXT'
usage: bash scripts/create_skill.sh --skill-id <id> --name <name> --description <description> [--force] [--dry-run]
TEXT
}

skill_id=""
skill_name=""
skill_description=""
force=0
dry_run=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skill-id)
      skill_id="$(sanitize_skill_id "${2:-}")"
      shift 2
      ;;
    --name)
      skill_name="${2:-}"
      shift 2
      ;;
    --description)
      skill_description="${2:-}"
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${skill_id}" || -z "${skill_name}" || -z "${skill_description}" ]]; then
  usage
  exit 1
fi

require_jq
ensure_state_dirs

skill_path="$(skill_root_path "${skill_id}")"
workspace_path="$(workspace_root_path "${skill_id}")"
if [[ -e "${skill_path}" && "${force}" -ne 1 ]]; then
  echo "error: ${skill_id} already exists; use --force to overwrite" >&2
  exit 1
fi

if [[ "${dry_run}" -eq 1 ]]; then
  echo "create_skill.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "skill_id=${skill_id}"
  echo "skill_path=${skill_id}"
  echo "workspace_path=.skills/workspaces/${skill_id}"
  exit 0
fi

rm -rf "${skill_path}"
rm -rf "${workspace_path}"
mkdir -p "${skill_path}/references" "${skill_path}/scripts"
mkdir -p "${workspace_path}"
cat > "${skill_path}/SKILL.md" <<MARKDOWN
---
name: ${skill_name}
description: ${skill_description}
---

# ${skill_name}

## When To Use

补充这个 skill 的触发条件和适用边界。

## Workflow

补充这个 skill 的核心步骤。
MARKDOWN

managed_revision="$(compute_directory_hash "${skill_path}")"
write_source_json "${skill_id}" "${skill_name}" "${skill_id}" "${managed_revision}" "" "local-created" "" "" "" "" true false
reset_risk_scan
write_report_md "${skill_id}" "${skill_name}" "${skill_description}" created "local-created" "" false "pending" "${skill_id}"
upsert_registry_entry "${skill_id}" "${skill_name}" "${skill_description}" created "${managed_revision}" pending false "${skill_id}"

echo "created ${skill_id}"
echo "skill_path=${skill_id}"
echo "workspace_path=.skills/workspaces/${skill_id}"
