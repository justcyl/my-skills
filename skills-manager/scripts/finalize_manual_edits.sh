#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

usage() {
  cat >&2 <<'TEXT'
usage: bash scripts/finalize_manual_edits.sh [--skill-id <id>] [--skip-distribute] [--publish] [--push] [--dry-run]
TEXT
}

skill_id=""
skip_distribute=0
publish=0
push=0
dry_run=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skill-id)
      skill_id="${2:-}"
      shift 2
      ;;
    --skip-distribute)
      skip_distribute=1
      shift
      ;;
    --publish)
      publish=1
      shift
      ;;
    --push)
      publish=1
      push=1
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

require_jq
ensure_state_dirs

if [[ -n "${skill_id}" ]]; then
  skill_ids=("${skill_id}")
else
  mapfile -t skill_ids < <(list_skill_ids)
fi

for current_skill_id in "${skill_ids[@]}"; do
  current_skill_path="$(skill_root_path "${current_skill_id}")"
  if [[ ! -f "${current_skill_path}/SKILL.md" ]]; then
    echo "warning: ${current_skill_id} has no SKILL.md, skipping" >&2
    continue
  fi

  skill_md_path="${current_skill_path}/SKILL.md"
  display_name="$(extract_frontmatter_value "${skill_md_path}" "name")"
  description="$(extract_frontmatter_value "${skill_md_path}" "description")"
  if [[ -z "${display_name}" ]]; then
    display_name="${current_skill_id}"
  fi

  source_path="$(source_json_path "${current_skill_id}")"
  source_type="local-manual"
  source_value=""
  source_url=""
  source_ref=""
  subpath=""
  bootstrap=true
  upstream_enabled=false
  upstream_revision=""
  status="managed"

  if [[ -f "${source_path}" ]]; then
    source_type="$(jq -r '.source_type // "local-manual"' "${source_path}")"
    source_value="$(jq -r '.source // ""' "${source_path}")"
    source_url="$(jq -r '.source_url // ""' "${source_path}")"
    source_ref="$(jq -r '.ref // ""' "${source_path}")"
    subpath="$(jq -r '.subpath // ""' "${source_path}")"
    bootstrap="$(jq -r '.bootstrap // true' "${source_path}")"
    upstream_enabled="$(jq -r '.upstream_enabled // false' "${source_path}")"
    upstream_revision="$(jq -r '.upstream_revision // ""' "${source_path}")"
    status="$(jq -r '.status // empty' "${source_path}" 2>/dev/null || true)"
  fi

  run_risk_scan "${current_skill_path}"
  managed_revision="$(compute_directory_hash "${current_skill_path}")"

  if [[ "${dry_run}" -eq 1 ]]; then
    echo "skill_id=${current_skill_id} managed_revision=${managed_revision} risk_status=${RISK_STATUS}"
    continue
  fi

  write_source_json "${current_skill_id}" "${display_name}" "${current_skill_id}" "${managed_revision}" "${upstream_revision}" "${source_type}" "${source_value}" "${source_url}" "${source_ref}" "${subpath}" "${bootstrap}" "${upstream_enabled}"
  write_report_md "${current_skill_id}" "${display_name}" "${description}" managed "${source_type}" "${source_value}" "${upstream_enabled}" "${RISK_STATUS}" "${current_skill_id}"
  upsert_registry_entry "${current_skill_id}" "${display_name}" "${description}" managed "${managed_revision}" "${RISK_STATUS}" "${upstream_enabled}" "${current_skill_id}"

done

if [[ "${dry_run}" -eq 1 ]]; then
  echo "repo_root=${REPO_ROOT}"
  echo "skill_filter=${skill_id:-all}"
  echo "publish=${publish}"
  echo "push=${push}"
  exit 0
fi

if [[ "${skip_distribute}" -ne 1 ]]; then
  if [[ -n "${skill_id}" ]]; then
    bash "${SCRIPT_DIR}/distribute_skills.sh" sync --skill-id "${skill_id}"
  else
    bash "${SCRIPT_DIR}/distribute_skills.sh" sync
  fi
fi

if [[ "${publish}" -eq 1 ]]; then
  publish_args=()
  if [[ "${push}" -eq 1 ]]; then
    publish_args+=(--push)
  fi
  bash "${SCRIPT_DIR}/publish_repo.sh" "${publish_args[@]}"
fi

echo "repo_root=${REPO_ROOT}"
echo "skill_filter=${skill_id:-all}"
echo "skip_distribute=${skip_distribute}"
echo "publish=${publish}"
echo "push=${push}"
