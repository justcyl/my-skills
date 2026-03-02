#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"
CATALOG_DIR="${REPO_ROOT}/catalog"
SKILLS_DIR="${CATALOG_DIR}/skills"
SOURCES_DIR="${CATALOG_DIR}/sources"
LOCKS_DIR="${CATALOG_DIR}/locks"
REGISTRY_PATH="${LOCKS_DIR}/registry.json"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

TARGET_SKILL_ID=""
CLEAR_DIRTY=0
DRY_RUN=0

usage() {
  cat >&2 <<'EOF'
usage: bash skills-manager/scripts/refresh_managed_state.sh [--skill-id <id>] [--clear-dirty] [--dry-run]
EOF
}

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required" >&2
  exit 1
fi

compute_directory_hash() {
  local dir_path="$1"

  (
    cd "${dir_path}"
    find . -type f ! -name '.DS_Store' | LC_ALL=C sort | while IFS= read -r file_path; do
      shasum -a 256 "${file_path}"
    done
  ) | shasum -a 256 | awk '{print "sha256:" $1}'
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skill-id)
      TARGET_SKILL_ID="${2:-}"
      shift 2
      ;;
    --clear-dirty)
      CLEAR_DIRTY=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
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

if [[ ! -f "${REGISTRY_PATH}" ]]; then
  echo "error: registry not found at ${REGISTRY_PATH}" >&2
  exit 1
fi

if [[ -n "${TARGET_SKILL_ID}" ]]; then
  SKILL_IDS=("${TARGET_SKILL_ID}")
else
  mapfile -t SKILL_IDS < <(jq -r '.skills | keys[]' "${REGISTRY_PATH}" | LC_ALL=C sort)
fi

updated_count=0

for skill_id in "${SKILL_IDS[@]}"; do
  managed_path="${SKILLS_DIR}/${skill_id}/managed"
  source_path="${SOURCES_DIR}/${skill_id}.json"

  if [[ ! -d "${managed_path}" || ! -f "${source_path}" ]]; then
    echo "warning: missing catalog state for ${skill_id}, skipping" >&2
    continue
  fi

  current_revision="$(compute_directory_hash "${managed_path}")"
  previous_revision="$(jq -r '.managed_revision // ""' "${source_path}")"

  managed_dirty="false"
  if [[ "${CLEAR_DIRTY}" -eq 1 ]]; then
    managed_dirty="false"
  elif [[ "${current_revision}" != "${previous_revision}" ]]; then
    managed_dirty="true"
  else
    managed_dirty="$(jq -r '.managed_dirty // false' "${source_path}")"
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "skill_id=${skill_id} previous_revision=${previous_revision} current_revision=${current_revision} managed_dirty=${managed_dirty}"
    continue
  fi

  source_temp="$(mktemp)"
  jq \
    --arg revision "${current_revision}" \
    --argjson dirty "${managed_dirty}" \
    --arg timestamp "${TIMESTAMP}" \
    '.managed_revision = $revision | .managed_dirty = $dirty | .last_imported_at = $timestamp' \
    "${source_path}" > "${source_temp}"
  mv "${source_temp}" "${source_path}"

  registry_temp="$(mktemp)"
  jq \
    --arg skill_id "${skill_id}" \
    --arg revision "${current_revision}" \
    --argjson dirty "${managed_dirty}" \
    --arg timestamp "${TIMESTAMP}" \
    '.skills[$skill_id].managed_revision = $revision
     | .skills[$skill_id].managed_dirty = $dirty
     | .skills[$skill_id].last_updated_at = $timestamp' \
    "${REGISTRY_PATH}" > "${registry_temp}"
  mv "${registry_temp}" "${REGISTRY_PATH}"

  updated_count="$((updated_count + 1))"
  echo "updated ${skill_id} managed_dirty=${managed_dirty}"
done

echo "repo_root=${REPO_ROOT}"
echo "skill_filter=${TARGET_SKILL_ID:-all}"
echo "clear_dirty=${CLEAR_DIRTY}"
echo "dry_run=${DRY_RUN}"
echo "updated_count=${updated_count}"
