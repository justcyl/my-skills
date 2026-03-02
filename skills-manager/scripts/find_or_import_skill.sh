#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

usage() {
  cat >&2 <<'TEXT'
usage:
  bash scripts/find_or_import_skill.sh search <query>
  bash scripts/find_or_import_skill.sh import <source> [--skill-id <id>] [--subpath <path>] [--ref <branch>] [--force] [--dry-run]
  bash scripts/find_or_import_skill.sh update --skill-id <id> [--allow-dirty] [--dry-run]
TEXT
}

command_search() {
  if [[ "$#" -eq 0 ]]; then
    echo "error: search requires a query" >&2
    exit 1
  fi
  npx skills find "$@"
}

command_import() {
  local source=""
  local skill_id_override=""
  local subpath_override=""
  local ref_override=""
  local force=0
  local dry_run=0
  local source_type=""
  local source_url=""
  local source_ref=""
  local upstream_revision=""

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --skill-id)
        skill_id_override="${2:-}"
        shift 2
        ;;
      --subpath)
        subpath_override="${2:-}"
        shift 2
        ;;
      --ref)
        ref_override="${2:-}"
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
        if [[ -z "${source}" ]]; then
          source="$1"
          shift
        else
          usage
          exit 1
        fi
        ;;
    esac
  done

  if [[ -z "${source}" ]]; then
    usage
    exit 1
  fi

  require_jq
  ensure_state_dirs

  detect_source "${source}"
  source_type="${DETECTED_SOURCE_TYPE}"
  source_url="${DETECTED_SOURCE_URL}"
  source_ref="${DETECTED_SOURCE_REF}"
  if [[ -n "${ref_override}" ]]; then
    source_ref="${ref_override}"
  fi
  if [[ -z "${subpath_override}" ]]; then
    subpath_override="${DETECTED_SUBPATH}"
  fi

  temp_dir="$(mktemp -d)"
  cleanup() {
    rm -rf "${temp_dir}"
  }
  trap cleanup EXIT

  stage_source "${source_type}" "${source_url}" "${source_ref}" "${temp_dir}"
  selected_dir="$(select_skill_dir "${temp_dir}" "${subpath_override}")"
  skill_md_path="${selected_dir}/SKILL.md"
  display_name="$(extract_frontmatter_value "${skill_md_path}" "name")"
  description="$(extract_frontmatter_value "${skill_md_path}" "description")"

  if [[ -z "${display_name}" ]]; then
    display_name="$(basename "${source%%.git}")"
  fi

  if [[ -n "${skill_id_override}" ]]; then
    skill_id="$(sanitize_skill_id "${skill_id_override}")"
  else
    skill_id="$(derive_default_skill_id "${selected_dir}" "${display_name}" "${source}" "${temp_dir}")"
  fi

  if [[ -z "${skill_id}" ]]; then
    echo "error: failed to derive skill id" >&2
    exit 1
  fi

  skill_path="$(skill_root_path "${skill_id}")"
  upstream_path="$(upstream_skill_path "${skill_id}")"

  if [[ -e "${skill_path}" && "${force}" -ne 1 ]]; then
    echo "error: skill '${skill_id}' already exists; use --force to overwrite" >&2
    exit 1
  fi

  run_risk_scan "${selected_dir}"

  if [[ "${source_type}" == "github" ]]; then
    upstream_revision="$(git -C "${temp_dir}" rev-parse HEAD 2>/dev/null || true)"
  fi
  if [[ -z "${upstream_revision}" ]]; then
    upstream_revision="$(compute_directory_hash "${selected_dir}")"
  fi

  if [[ "${dry_run}" -eq 1 ]]; then
    echo "find_or_import_skill.sh import"
    echo "repo_root=${REPO_ROOT}"
    echo "source=${source}"
    echo "source_type=${source_type}"
    echo "source_url=${source_url}"
    echo "ref=${source_ref}"
    echo "subpath=${subpath_override}"
    echo "skill_id=${skill_id}"
    echo "skill_path=${skill_id}"
    echo "upstream_path=.skills/upstream/${skill_id}"
    echo "risk_status=${RISK_STATUS}"
    if [[ "${#RISK_FINDINGS[@]}" -gt 0 ]]; then
      printf 'risk_findings=%s\n' "$(IFS='; '; echo "${RISK_FINDINGS[*]}")"
    fi
    exit 0
  fi

  rm -rf "${skill_path}" "${upstream_path}"
  mkdir -p "${upstream_path}"
  cp -R "${selected_dir}/." "${skill_path}/"
  cp -R "${selected_dir}/." "${upstream_path}/"

  managed_revision="$(compute_directory_hash "${skill_path}")"

  write_source_json "${skill_id}" "${display_name}" "${skill_id}" "${managed_revision}" "${upstream_revision}" "${source_type}" "${source}" "${source_url}" "${source_ref}" "${subpath_override}" false true
  write_report_md "${skill_id}" "${display_name}" "${description}" imported "${source_type}" "${source}" true "${RISK_STATUS}" "${skill_id}"
  upsert_registry_entry "${skill_id}" "${display_name}" "${description}" imported "${managed_revision}" "${RISK_STATUS}" true "${skill_id}"

  echo "imported ${skill_id}"
  echo "skill_path=${skill_id}"
  echo "upstream_path=.skills/upstream/${skill_id}"
  echo "risk_status=${RISK_STATUS}"
}

command_update() {
  local skill_id=""
  local allow_dirty=0
  local dry_run=0

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --skill-id)
        skill_id="${2:-}"
        shift 2
        ;;
      --allow-dirty)
        allow_dirty=1
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

  if [[ -z "${skill_id}" ]]; then
    usage
    exit 1
  fi

  require_jq
  ensure_state_dirs

  source_path="$(source_json_path "${skill_id}")"
  if [[ ! -f "${source_path}" ]]; then
    echo "error: missing source metadata for ${skill_id}" >&2
    exit 1
  fi

  upstream_enabled="$(jq -r '.upstream_enabled // false' "${source_path}")"
  if [[ "${upstream_enabled}" != "true" ]]; then
    echo "error: ${skill_id} does not have an upstream source enabled" >&2
    exit 1
  fi

  current_skill_path="$(skill_root_path "${skill_id}")"
  if [[ ! -d "${current_skill_path}" ]]; then
    echo "error: missing root skill directory for ${skill_id}" >&2
    exit 1
  fi

  current_revision="$(compute_directory_hash "${current_skill_path}")"
  previous_revision="$(jq -r '.managed_revision // ""' "${source_path}")"
  if [[ "${current_revision}" != "${previous_revision}" && "${allow_dirty}" -ne 1 ]]; then
    echo "error: ${skill_id} has unfinalized manual edits; rerun with --allow-dirty to overwrite" >&2
    exit 1
  fi

  source_value="$(jq -r '.source // ""' "${source_path}")"
  source_ref="$(jq -r '.ref // ""' "${source_path}")"
  subpath="$(jq -r '.subpath // ""' "${source_path}")"

  args=(import "${source_value}" --skill-id "${skill_id}" --force)
  if [[ -n "${source_ref}" ]]; then
    args+=(--ref "${source_ref}")
  fi
  if [[ -n "${subpath}" ]]; then
    args+=(--subpath "${subpath}")
  fi
  if [[ "${dry_run}" -eq 1 ]]; then
    args+=(--dry-run)
  fi

  echo "find_or_import_skill.sh update"
  echo "skill_id=${skill_id}"
  echo "allow_dirty=${allow_dirty}"
  echo "dry_run=${dry_run}"
  bash "$0" "${args[@]}"
}

subcommand="${1:-}"
if [[ -z "${subcommand}" ]]; then
  usage
  exit 1
fi
shift

case "${subcommand}" in
  search)
    command_search "$@"
    ;;
  import)
    command_import "$@"
    ;;
  update)
    command_update "$@"
    ;;
  *)
    usage
    exit 1
    ;;
esac
