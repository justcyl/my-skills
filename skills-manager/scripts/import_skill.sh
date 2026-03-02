#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"
CATALOG_DIR="${REPO_ROOT}/catalog"
SKILLS_DIR="${CATALOG_DIR}/skills"
SOURCES_DIR="${CATALOG_DIR}/sources"
REPORTS_DIR="${CATALOG_DIR}/reports"
LOCKS_DIR="${CATALOG_DIR}/locks"
REGISTRY_PATH="${LOCKS_DIR}/registry.json"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

SOURCE=""
SKILL_ID_OVERRIDE=""
SUBPATH_OVERRIDE=""
REF_OVERRIDE=""
FORCE=0
DRY_RUN=0
SOURCE_TYPE=""
SOURCE_URL=""
SOURCE_REF=""
RISK_STATUS="passed"
RISK_FINDINGS=()

usage() {
  cat >&2 <<'EOF'
usage: bash skills-manager/scripts/import_skill.sh <source> [--skill-id <id>] [--subpath <path>] [--ref <branch>] [--force] [--dry-run]
EOF
}

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required" >&2
  exit 1
fi

sanitize_skill_id() {
  local raw="$1"
  printf '%s' "${raw}" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9._-]+/-/g; s/^[.-]+//; s/[.-]+$//'
}

extract_frontmatter_value() {
  local file_path="$1"
  local key="$2"

  awk -v search_key="${key}" '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && index($0, search_key ":") == 1 {
      value = substr($0, length(search_key) + 2)
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      gsub(/^"/, "", value)
      gsub(/"$/, "", value)
      gsub(/^'\''/, "", value)
      gsub(/'\''$/, "", value)
      print value
      exit
    }
  ' "${file_path}"
}

compute_directory_hash() {
  local dir_path="$1"

  (
    cd "${dir_path}"
    find . -type f ! -name '.DS_Store' | LC_ALL=C sort | while IFS= read -r file_path; do
      shasum -a 256 "${file_path}"
    done
  ) | shasum -a 256 | awk '{print "sha256:" $1}'
}

derive_default_skill_id() {
  local selected_dir="$1"
  local display_name="$2"
  local source="$3"
  local temp_dir="$4"
  local candidate=""

  if [[ -n "${display_name}" ]]; then
    candidate="$(sanitize_skill_id "${display_name}")"
  fi

  if [[ -z "${candidate}" ]]; then
    if [[ "${selected_dir}" == "${temp_dir}" ]]; then
      candidate="$(sanitize_skill_id "$(basename "${source%%.git}")")"
    else
      candidate="$(sanitize_skill_id "$(basename "${selected_dir}")")"
    fi
  fi

  printf '%s\n' "${candidate}"
}

detect_source() {
  local source="$1"

  if [[ "${source}" == /* || "${source}" == ./* || "${source}" == ../* ]]; then
    SOURCE_TYPE="local"
    SOURCE_URL="$(cd "$(dirname "${source}")" && pwd)/$(basename "${source}")"
    return
  fi

  if [[ -d "${source}" ]]; then
    SOURCE_TYPE="local"
    SOURCE_URL="$(cd "${source}" && pwd)"
    return
  fi

  if [[ "${source}" =~ ^https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)$ ]]; then
    SOURCE_TYPE="github"
    SOURCE_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    SOURCE_REF="${BASH_REMATCH[3]}"
    if [[ -z "${SUBPATH_OVERRIDE}" ]]; then
      SUBPATH_OVERRIDE="${BASH_REMATCH[4]}"
    fi
    return
  fi

  if [[ "${source}" =~ ^https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)$ ]]; then
    SOURCE_TYPE="github"
    SOURCE_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    SOURCE_REF="${BASH_REMATCH[3]}"
    return
  fi

  if [[ "${source}" =~ ^https://github\.com/([^/]+)/([^/]+)(\.git)?/?$ ]]; then
    SOURCE_TYPE="github"
    SOURCE_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    return
  fi

  if [[ "${source}" =~ ^[^/]+/[^/]+$ ]]; then
    SOURCE_TYPE="github"
    SOURCE_URL="https://github.com/${source}.git"
    return
  fi

  echo "error: unsupported source '${source}'" >&2
  exit 1
}

stage_source() {
  local source="$1"
  local temp_dir="$2"

  case "${SOURCE_TYPE}" in
    local)
      cp -R "${SOURCE_URL}/." "${temp_dir}/"
      ;;
    github)
      if [[ -n "${SOURCE_REF}" ]]; then
        git clone --depth 1 --branch "${SOURCE_REF}" "${SOURCE_URL}" "${temp_dir}" >/dev/null 2>&1
      else
        git clone --depth 1 "${SOURCE_URL}" "${temp_dir}" >/dev/null 2>&1
      fi
      ;;
    *)
      echo "error: source type '${SOURCE_TYPE}' is not implemented" >&2
      exit 1
      ;;
  esac
}

select_skill_dir() {
  local staged_root="$1"
  local selected_path=""

  if [[ -n "${SUBPATH_OVERRIDE}" ]]; then
    selected_path="${staged_root}/${SUBPATH_OVERRIDE}"
    if [[ ! -f "${selected_path}/SKILL.md" ]]; then
      echo "error: subpath '${SUBPATH_OVERRIDE}' does not contain SKILL.md" >&2
      exit 1
    fi
    printf '%s\n' "${selected_path}"
    return
  fi

  if [[ -f "${staged_root}/SKILL.md" ]]; then
    printf '%s\n' "${staged_root}"
    return
  fi

  mapfile -t skill_files < <(find "${staged_root}" -type f -name 'SKILL.md' -not -path '*/.git/*' | LC_ALL=C sort)

  if [[ "${#skill_files[@]}" -eq 0 ]]; then
    echo "error: no SKILL.md found in source" >&2
    exit 1
  fi

  if [[ "${#skill_files[@]}" -gt 1 ]]; then
    echo "error: multiple SKILL.md files found; use --subpath to disambiguate" >&2
    printf 'candidates:\n' >&2
    for file_path in "${skill_files[@]}"; do
      printf '  - %s\n' "${file_path#${staged_root}/}" >&2
    done
    exit 1
  fi

  printf '%s\n' "$(dirname "${skill_files[0]}")"
}

maybe_add_finding() {
  local severity="$1"
  local label="$2"
  local matched="$3"

  if [[ "${matched}" == "1" ]]; then
    RISK_FINDINGS+=("${label}")
    if [[ "${severity}" == "blocked" ]]; then
      RISK_STATUS="blocked"
    elif [[ "${severity}" == "warned" && "${RISK_STATUS}" != "blocked" ]]; then
      RISK_STATUS="warned"
    fi
  fi
}

scan_pattern() {
  local dir_path="$1"
  local regex="$2"
  local matched="0"

  while IFS= read -r file_path; do
    if awk -v regex="${regex}" '
      BEGIN { IGNORECASE = 1 }
      $0 ~ regex { found = 1; exit }
      END { exit(found ? 0 : 1) }
    ' "${file_path}"; then
      matched="1"
      break
    fi
  done < <(find "${dir_path}" -type f -not -path '*/.git/*' | LC_ALL=C sort)

  printf '%s\n' "${matched}"
}

run_risk_scan() {
  local dir_path="$1"

  maybe_add_finding "warned" "references sensitive ssh or aws paths" "$(scan_pattern "${dir_path}" "(~/.ssh|~/.aws|\\.ssh/|\\.aws/)")"
  maybe_add_finding "warned" "mentions secrets, tokens, or private keys" "$(scan_pattern "${dir_path}" "(api[_ -]?key|secret|token|private key)")"
  maybe_add_finding "blocked" "downloads and executes remote content" "$(scan_pattern "${dir_path}" "(curl[[:space:]].*[|][[:space:]]*(sh|bash|zsh)|wget[[:space:]].*[|][[:space:]]*(sh|bash|zsh))")"
  maybe_add_finding "blocked" "requests bypassing policy or restrictions" "$(scan_pattern "${dir_path}" "(ignore .*policy|bypass .*safety|override .*restriction)")"
}

write_source_json() {
  local skill_id="$1"
  local display_name="$2"
  local managed_revision="$3"
  local upstream_revision="$4"
  local source_type="$5"
  local source_value="$6"
  local source_url="$7"
  local source_ref="$8"
  local subpath="$9"

  jq -n \
    --arg skill_id "${skill_id}" \
    --arg display_name "${display_name}" \
    --arg managed_revision "${managed_revision}" \
    --arg upstream_revision "${upstream_revision}" \
    --arg source_type "${source_type}" \
    --arg source_value "${source_value}" \
    --arg source_url "${source_url}" \
    --arg source_ref "${source_ref}" \
    --arg subpath "${subpath}" \
    --arg timestamp "${TIMESTAMP}" \
    '{
      skill_id: $skill_id,
      display_name: $display_name,
      source_type: $source_type,
      source: $source_value,
      source_url: $source_url,
      ref: $source_ref,
      subpath: $subpath,
      bootstrap: false,
      upstream_enabled: true,
      last_imported_at: $timestamp,
      upstream_revision: $upstream_revision,
      managed_revision: $managed_revision,
      managed_dirty: false
    }' > "${SOURCES_DIR}/${skill_id}.json"
}

write_report_md() {
  local skill_id="$1"
  local display_name="$2"
  local description="$3"
  local source_type="$4"
  local source_value="$5"
  local risk_status="$6"

  {
    printf '# %s\n\n' "${display_name}"
    printf -- '- skill_id: `%s`\n' "${skill_id}"
    printf -- '- status: imported\n'
    printf -- '- source_type: `%s`\n' "${source_type}"
    printf -- '- source: `%s`\n' "${source_value}"
    printf -- '- risk_status: `%s`\n' "${risk_status}"
    printf -- '- managed_path: `catalog/skills/%s/managed`\n\n' "${skill_id}"
    printf '## Summary\n\n%s\n\n' "${description:-No description found in frontmatter.}"
    printf '## Risk Findings\n\n'

    if [[ "${#RISK_FINDINGS[@]}" -eq 0 ]]; then
      printf -- '- No heuristic findings.\n'
    else
      for finding in "${RISK_FINDINGS[@]}"; do
        printf -- '- %s\n' "${finding}"
      done
    fi

    printf '\n## Notes\n\n'
    printf -- '- Upstream was copied into `catalog/skills/%s/upstream/`.\n' "${skill_id}"
    printf -- '- Managed was seeded from upstream and should be refined by the agent into a Chinese optimized version.\n'
  } > "${REPORTS_DIR}/${skill_id}.md"
}

update_registry_entry() {
  local skill_id="$1"
  local display_name="$2"
  local description="$3"
  local managed_revision="$4"
  local risk_status="$5"
  local temp_file

  temp_file="$(mktemp)"

  jq \
    --arg skill_id "${skill_id}" \
    --arg display_name "${display_name}" \
    --arg description "${description}" \
    --arg managed_revision "${managed_revision}" \
    --arg risk_status "${risk_status}" \
    --arg timestamp "${TIMESTAMP}" \
    '.skills[$skill_id] = {
      display_name: $display_name,
      description: $description,
      status: "imported",
      audit_status: $risk_status,
      managed_dirty: false,
      has_upstream: true,
      distribution: {},
      report_path: ("catalog/reports/" + $skill_id + ".md"),
      source_path: ("catalog/sources/" + $skill_id + ".json"),
      managed_path: ("catalog/skills/" + $skill_id + "/managed"),
      upstream_path: ("catalog/skills/" + $skill_id + "/upstream"),
      managed_revision: $managed_revision,
      last_updated_at: $timestamp
    }' "${REGISTRY_PATH}" > "${temp_file}"

  mv "${temp_file}" "${REGISTRY_PATH}"
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skill-id)
      SKILL_ID_OVERRIDE="${2:-}"
      shift 2
      ;;
    --subpath)
      SUBPATH_OVERRIDE="${2:-}"
      shift 2
      ;;
    --ref)
      REF_OVERRIDE="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
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
      if [[ -z "${SOURCE}" ]]; then
        SOURCE="$1"
        shift
      else
        usage
        exit 1
      fi
      ;;
  esac
done

if [[ -z "${SOURCE}" ]]; then
  usage
  exit 1
fi

mkdir -p "${SKILLS_DIR}" "${SOURCES_DIR}" "${REPORTS_DIR}" "${LOCKS_DIR}"

if [[ ! -f "${REGISTRY_PATH}" ]]; then
  cat > "${REGISTRY_PATH}" <<'EOF'
{
  "version": 1,
  "skills": {}
}
EOF
fi

detect_source "${SOURCE}"

if [[ -n "${REF_OVERRIDE}" ]]; then
  SOURCE_REF="${REF_OVERRIDE}"
fi

TEMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${TEMP_DIR}"
}
trap cleanup EXIT

stage_source "${SOURCE}" "${TEMP_DIR}"
SELECTED_DIR="$(select_skill_dir "${TEMP_DIR}")"
SKILL_MD_PATH="${SELECTED_DIR}/SKILL.md"
DISPLAY_NAME="$(extract_frontmatter_value "${SKILL_MD_PATH}" "name")"
DESCRIPTION="$(extract_frontmatter_value "${SKILL_MD_PATH}" "description")"

if [[ -z "${DISPLAY_NAME}" ]]; then
  DISPLAY_NAME="$(basename "${SOURCE%%.git}")"
fi

if [[ -n "${SKILL_ID_OVERRIDE}" ]]; then
  SKILL_ID="$(sanitize_skill_id "${SKILL_ID_OVERRIDE}")"
else
  SKILL_ID="$(derive_default_skill_id "${SELECTED_DIR}" "${DISPLAY_NAME}" "${SOURCE}" "${TEMP_DIR}")"
fi

if [[ -z "${SKILL_ID}" ]]; then
  echo "error: failed to derive skill id" >&2
  exit 1
fi

run_risk_scan "${SELECTED_DIR}"

DESTINATION_ROOT="${SKILLS_DIR}/${SKILL_ID}"
UPSTREAM_DIR="${DESTINATION_ROOT}/upstream"
MANAGED_DIR="${DESTINATION_ROOT}/managed"

if [[ -e "${DESTINATION_ROOT}" && "${FORCE}" -ne 1 ]]; then
  echo "error: skill '${SKILL_ID}' already exists; use --force to overwrite" >&2
  exit 1
fi

UPSTREAM_REVISION=""
if [[ "${SOURCE_TYPE}" == "github" ]]; then
  UPSTREAM_REVISION="$(git -C "${TEMP_DIR}" rev-parse HEAD 2>/dev/null || true)"
fi

if [[ -z "${UPSTREAM_REVISION}" ]]; then
  UPSTREAM_REVISION="$(compute_directory_hash "${SELECTED_DIR}")"
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "import_skill.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "source=${SOURCE}"
  echo "source_type=${SOURCE_TYPE}"
  echo "source_url=${SOURCE_URL}"
  echo "ref=${SOURCE_REF}"
  echo "selected_dir=${SELECTED_DIR}"
  echo "skill_id=${SKILL_ID}"
  echo "display_name=${DISPLAY_NAME}"
  echo "risk_status=${RISK_STATUS}"
  if [[ "${#RISK_FINDINGS[@]}" -gt 0 ]]; then
    printf 'risk_findings=%s\n' "$(IFS='; '; echo "${RISK_FINDINGS[*]}")"
  fi
  exit 0
fi

rm -rf "${DESTINATION_ROOT}"
mkdir -p "${UPSTREAM_DIR}" "${MANAGED_DIR}"
cp -R "${SELECTED_DIR}/." "${UPSTREAM_DIR}/"
cp -R "${SELECTED_DIR}/." "${MANAGED_DIR}/"

MANAGED_REVISION="$(compute_directory_hash "${MANAGED_DIR}")"

write_source_json \
  "${SKILL_ID}" \
  "${DISPLAY_NAME}" \
  "${MANAGED_REVISION}" \
  "${UPSTREAM_REVISION}" \
  "${SOURCE_TYPE}" \
  "${SOURCE}" \
  "${SOURCE_URL}" \
  "${SOURCE_REF}" \
  "${SUBPATH_OVERRIDE}"

write_report_md \
  "${SKILL_ID}" \
  "${DISPLAY_NAME}" \
  "${DESCRIPTION}" \
  "${SOURCE_TYPE}" \
  "${SOURCE}" \
  "${RISK_STATUS}"

update_registry_entry \
  "${SKILL_ID}" \
  "${DISPLAY_NAME}" \
  "${DESCRIPTION}" \
  "${MANAGED_REVISION}" \
  "${RISK_STATUS}"

echo "imported ${SKILL_ID}"
echo "source_type=${SOURCE_TYPE}"
echo "risk_status=${RISK_STATUS}"
echo "managed_path=${MANAGED_DIR}"
