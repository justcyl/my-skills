#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"
SOURCES_DIR="${REPO_ROOT}/catalog/sources"
IMPORT_SCRIPT="${SCRIPT_DIR}/import_skill.sh"

TARGET_SKILL_ID=""
ALLOW_DIRTY=0
DRY_RUN=0

usage() {
  cat >&2 <<'EOF'
usage: bash skills-manager/scripts/update_skill.sh --skill-id <id> [--allow-dirty] [--dry-run]
EOF
}

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required" >&2
  exit 1
fi

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skill-id)
      TARGET_SKILL_ID="${2:-}"
      shift 2
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
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

if [[ -z "${TARGET_SKILL_ID}" ]]; then
  usage
  exit 1
fi

SOURCE_PATH="${SOURCES_DIR}/${TARGET_SKILL_ID}.json"

if [[ ! -f "${SOURCE_PATH}" ]]; then
  echo "error: missing source metadata for ${TARGET_SKILL_ID}" >&2
  exit 1
fi

SOURCE_TYPE="$(jq -r '.source_type // ""' "${SOURCE_PATH}")"
UPSTREAM_ENABLED="$(jq -r '.upstream_enabled // false' "${SOURCE_PATH}")"
MANAGED_DIRTY="$(jq -r '.managed_dirty // false' "${SOURCE_PATH}")"
SOURCE_VALUE="$(jq -r '.source // ""' "${SOURCE_PATH}")"
SOURCE_URL="$(jq -r '.source_url // ""' "${SOURCE_PATH}")"
SOURCE_REF="$(jq -r '.ref // ""' "${SOURCE_PATH}")"
SUBPATH="$(jq -r '.subpath // ""' "${SOURCE_PATH}")"

if [[ "${UPSTREAM_ENABLED}" != "true" ]]; then
  echo "error: ${TARGET_SKILL_ID} does not have an upstream source enabled" >&2
  exit 1
fi

if [[ "${MANAGED_DIRTY}" == "true" && "${ALLOW_DIRTY}" -ne 1 ]]; then
  echo "error: ${TARGET_SKILL_ID} has managed_dirty=true; rerun with --allow-dirty to overwrite" >&2
  exit 1
fi

RESOLVED_SOURCE="${SOURCE_VALUE}"
if [[ -z "${RESOLVED_SOURCE}" ]]; then
  RESOLVED_SOURCE="${SOURCE_URL}"
fi

if [[ -z "${RESOLVED_SOURCE}" ]]; then
  echo "error: ${TARGET_SKILL_ID} has no usable source value" >&2
  exit 1
fi

ARGS=("${RESOLVED_SOURCE}" "--skill-id" "${TARGET_SKILL_ID}" "--force")

if [[ -n "${SUBPATH}" ]]; then
  ARGS+=("--subpath" "${SUBPATH}")
fi

if [[ -n "${SOURCE_REF}" ]]; then
  ARGS+=("--ref" "${SOURCE_REF}")
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  ARGS+=("--dry-run")
fi

echo "update_skill.sh"
echo "repo_root=${REPO_ROOT}"
echo "skill_id=${TARGET_SKILL_ID}"
echo "source_type=${SOURCE_TYPE}"
echo "source=${RESOLVED_SOURCE}"
echo "allow_dirty=${ALLOW_DIRTY}"
echo "dry_run=${DRY_RUN}"

bash "${IMPORT_SCRIPT}" "${ARGS[@]}"
