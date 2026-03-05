#!/usr/bin/env bash
set -euo pipefail

realpath_compat() {
  python3 - "$1" <<'PY'
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
}

SCRIPT_FILE="$(realpath_compat "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_FILE}")" && pwd)"
SCRIPTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILL_DIR="$(cd "${SCRIPTS_DIR}/.." && pwd)"
SCRIPT_BASE_REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"

# 默认把 my-skills 作为统一技能仓库；可通过环境变量覆盖。
PREFERRED_REPO_ROOT="${MY_SKILLS_REPO_ROOT:-/Users/chenyl/project/my-skills}"
if [[ -f "${PREFERRED_REPO_ROOT}/skills-manager/SKILL.md" ]]; then
  REPO_ROOT="${PREFERRED_REPO_ROOT}"
else
  REPO_ROOT="${SCRIPT_BASE_REPO_ROOT}"
fi

STATE_DIR="${REPO_ROOT}/.skills"
ARCHIVED_SKILLS_DIR="${REPO_ROOT}/archived-skills"
SOURCES_DIR="${STATE_DIR}/sources"
REPORTS_DIR="${STATE_DIR}/reports"
AGENTS_DIR="${STATE_DIR}/agents"
UPSTREAM_DIR="${STATE_DIR}/upstream"
REGISTRY_PATH="${STATE_DIR}/registry.json"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

RISK_STATUS="passed"
declare -a RISK_FINDINGS=()

require_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "error: jq is required" >&2
    exit 1
  fi
}

ensure_state_dirs() {
  mkdir -p "${STATE_DIR}" "${ARCHIVED_SKILLS_DIR}" "${SOURCES_DIR}" "${REPORTS_DIR}" "${AGENTS_DIR}" "${UPSTREAM_DIR}"
  if [[ ! -f "${REGISTRY_PATH}" ]]; then
    cat > "${REGISTRY_PATH}" <<'JSON'
{
  "version": 2,
  "skills": {}
}
JSON
  fi
  for agent in codex claude-code; do
    if [[ ! -f "${AGENTS_DIR}/${agent}.json" ]]; then
      cat > "${AGENTS_DIR}/${agent}.json" <<'JSON'
{
  "agent": "",
  "skills": {}
}
JSON
      temp_file="$(mktemp)"
      jq --arg agent "${agent}" '.agent = $agent' "${AGENTS_DIR}/${agent}.json" > "${temp_file}"
      mv "${temp_file}" "${AGENTS_DIR}/${agent}.json"
    fi
  done
}

sanitize_skill_id() {
  local raw="$1"
  printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^[.-]+//; s/[.-]+$//'
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

list_skill_ids() {
  local dir_path
  for dir_path in "${REPO_ROOT}"/*; do
    [[ -d "${dir_path}" ]] || continue
    [[ -f "${dir_path}/SKILL.md" ]] || continue
    basename "${dir_path}"
  done | LC_ALL=C sort
}

skill_root_path() {
  local skill_id="$1"
  printf '%s\n' "${REPO_ROOT}/${skill_id}"
}

archived_skill_path() {
  local skill_id="$1"
  printf '%s\n' "${ARCHIVED_SKILLS_DIR}/${skill_id}"
}

source_json_path() {
  local skill_id="$1"
  printf '%s\n' "${SOURCES_DIR}/${skill_id}.json"
}

report_md_path() {
  local skill_id="$1"
  printf '%s\n' "${REPORTS_DIR}/${skill_id}.md"
}

upstream_skill_path() {
  local skill_id="$1"
  printf '%s\n' "${UPSTREAM_DIR}/${skill_id}"
}

reset_risk_scan() {
  RISK_STATUS="passed"
  RISK_FINDINGS=()
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
      $0 ~ regex && $0 !~ /(scan_pattern|maybe_add_finding)/ { found = 1; exit }
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
  reset_risk_scan
  maybe_add_finding "warned" "references sensitive ssh or aws paths" "$(scan_pattern "${dir_path}" "(~/.ssh|~/.aws|\\.ssh/|\\.aws/)")"
  maybe_add_finding "warned" "mentions secrets, tokens, or private keys" "$(scan_pattern "${dir_path}" "(api[_ -]?key|secret|token|private key)")"
  maybe_add_finding "blocked" "downloads and executes remote content" "$(scan_pattern "${dir_path}" "(curl[[:space:]].*[|][[:space:]]*(sh|bash|zsh)|wget[[:space:]].*[|][[:space:]]*(sh|bash|zsh))")"
  maybe_add_finding "blocked" "requests bypassing policy or restrictions" "$(scan_pattern "${dir_path}" "(ignore .*policy|bypass .*safety|override .*restriction)")"
}

detect_source() {
  local source="$1"
  DETECTED_SOURCE_TYPE=""
  DETECTED_SOURCE_URL=""
  DETECTED_SOURCE_REF=""
  DETECTED_SUBPATH=""

  if [[ "${source}" == /* || "${source}" == ./* || "${source}" == ../* ]]; then
    DETECTED_SOURCE_TYPE="local"
    DETECTED_SOURCE_URL="$(cd "$(dirname "${source}")" && pwd)/$(basename "${source}")"
    return
  fi

  if [[ -d "${source}" ]]; then
    DETECTED_SOURCE_TYPE="local"
    DETECTED_SOURCE_URL="$(cd "${source}" && pwd)"
    return
  fi

  if [[ "${source}" =~ ^https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)$ ]]; then
    DETECTED_SOURCE_TYPE="github"
    DETECTED_SOURCE_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    DETECTED_SOURCE_REF="${BASH_REMATCH[3]}"
    DETECTED_SUBPATH="${BASH_REMATCH[4]}"
    return
  fi

  if [[ "${source}" =~ ^https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)$ ]]; then
    DETECTED_SOURCE_TYPE="github"
    DETECTED_SOURCE_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    DETECTED_SOURCE_REF="${BASH_REMATCH[3]}"
    return
  fi

  if [[ "${source}" =~ ^https://github\.com/([^/]+)/([^/]+)(\.git)?/?$ ]]; then
    DETECTED_SOURCE_TYPE="github"
    DETECTED_SOURCE_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    return
  fi

  if [[ "${source}" =~ ^[^/]+/[^/]+$ ]]; then
    DETECTED_SOURCE_TYPE="github"
    DETECTED_SOURCE_URL="https://github.com/${source}.git"
    return
  fi

  echo "error: unsupported source '${source}'" >&2
  exit 1
}

stage_source() {
  local source_type="$1"
  local source_url="$2"
  local source_ref="$3"
  local temp_dir="$4"

  case "${source_type}" in
    local)
      cp -R "${source_url}/." "${temp_dir}/"
      ;;
    github)
      if [[ -n "${source_ref}" ]]; then
        git clone --depth 1 --branch "${source_ref}" "${source_url}" "${temp_dir}" >/dev/null 2>&1
      else
        git clone --depth 1 "${source_url}" "${temp_dir}" >/dev/null 2>&1
      fi
      ;;
    *)
      echo "error: source type '${source_type}' is not implemented" >&2
      exit 1
      ;;
  esac
}

select_skill_dir() {
  local staged_root="$1"
  local subpath_override="$2"

  if [[ -n "${subpath_override}" ]]; then
    selected_path="${staged_root}/${subpath_override}"
    if [[ ! -f "${selected_path}/SKILL.md" ]]; then
      echo "error: subpath '${subpath_override}' does not contain SKILL.md" >&2
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

write_source_json() {
  local skill_id="$1"
  local display_name="$2"
  local skill_path="$3"
  local managed_revision="$4"
  local upstream_revision="$5"
  local source_type="$6"
  local source_value="$7"
  local source_url="$8"
  local source_ref="$9"
  local subpath="${10}"
  local bootstrap_flag="${11}"
  local upstream_enabled="${12}"
  local source_path

  source_path="$(source_json_path "${skill_id}")"

  jq -n \
    --arg skill_id "${skill_id}" \
    --arg display_name "${display_name}" \
    --arg skill_path "${skill_path}" \
    --arg managed_revision "${managed_revision}" \
    --arg upstream_revision "${upstream_revision}" \
    --arg source_type "${source_type}" \
    --arg source_value "${source_value}" \
    --arg source_url "${source_url}" \
    --arg source_ref "${source_ref}" \
    --arg subpath "${subpath}" \
    --arg timestamp "${TIMESTAMP}" \
    --arg upstream_path ".skills/upstream/${skill_id}" \
    --argjson bootstrap "${bootstrap_flag}" \
    --argjson upstream_enabled "${upstream_enabled}" \
    '{
      skill_id: $skill_id,
      display_name: $display_name,
      skill_path: $skill_path,
      source_type: $source_type,
      source: $source_value,
      source_url: $source_url,
      ref: $source_ref,
      subpath: $subpath,
      bootstrap: $bootstrap,
      upstream_enabled: $upstream_enabled,
      upstream_path: $upstream_path,
      last_imported_at: $timestamp,
      upstream_revision: $upstream_revision,
      managed_revision: $managed_revision,
      managed_dirty: false
    }' > "${source_path}"
}

write_report_md() {
  local skill_id="$1"
  local display_name="$2"
  local description="$3"
  local status="$4"
  local source_type="$5"
  local source_value="$6"
  local upstream_enabled="$7"
  local risk_status="$8"
  local skill_path="$9"

  {
    printf '# %s\n\n' "${display_name}"
    printf -- '- skill_id: `%s`\n' "${skill_id}"
    printf -- '- status: `%s`\n' "${status}"
    printf -- '- skill_path: `%s`\n' "${skill_path}"
    printf -- '- source_type: `%s`\n' "${source_type}"
    printf -- '- source: `%s`\n' "${source_value}"
    printf -- '- upstream_enabled: `%s`\n' "${upstream_enabled}"
    printf -- '- risk_status: `%s`\n\n' "${risk_status}"
    printf '## Summary\n\n%s\n\n' "${description:-No description found in frontmatter.}"
    printf '## Risk Findings\n\n'
    if [[ "${#RISK_FINDINGS[@]}" -eq 0 ]]; then
      printf -- '- No heuristic findings.\n'
    else
      for finding in "${RISK_FINDINGS[@]}"; do
        printf -- '- %s\n' "${finding}"
      done
    fi
    printf '\n## Boundaries\n\n'
    printf -- '- Script-generated state lives in `.skills/`.\n'
    printf -- '- Skill content lives directly in `%s/`.\n' "${skill_path}"
    printf -- '- LLM review should focus on semantics, prompt safety, and Chinese optimization.\n'
  } > "$(report_md_path "${skill_id}")"
}

upsert_registry_entry() {
  local skill_id="$1"
  local display_name="$2"
  local description="$3"
  local status="$4"
  local managed_revision="$5"
  local risk_status="$6"
  local has_upstream="$7"
  local skill_path="$8"
  local temp_file

  temp_file="$(mktemp)"

  jq \
    --arg skill_id "${skill_id}" \
    --arg display_name "${display_name}" \
    --arg description "${description}" \
    --arg status "${status}" \
    --arg managed_revision "${managed_revision}" \
    --arg risk_status "${risk_status}" \
    --arg skill_path "${skill_path}" \
    --arg timestamp "${TIMESTAMP}" \
    --argjson has_upstream "${has_upstream}" \
    '.skills[$skill_id] = ((.skills[$skill_id] // {distribution: {}}) + {
      display_name: $display_name,
      description: $description,
      status: $status,
      audit_status: $risk_status,
      managed_dirty: false,
      has_upstream: $has_upstream,
      report_path: (".skills/reports/" + $skill_id + ".md"),
      source_path: (".skills/sources/" + $skill_id + ".json"),
      skill_path: $skill_path,
      upstream_path: (".skills/upstream/" + $skill_id),
      managed_revision: $managed_revision,
      last_updated_at: $timestamp,
      distribution: ((.skills[$skill_id].distribution // {}))
    })' "${REGISTRY_PATH}" > "${temp_file}"

  mv "${temp_file}" "${REGISTRY_PATH}"
}

resolve_agent_target_dir() {
  local agent="$1"
  case "${agent}" in
    codex)
      printf '%s\n' "${CODEX_SKILLS_DIR:-${HOME}/.codex/skills}"
      ;;
    claude-code)
      printf '%s\n' "${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}"
      ;;
    *)
      echo "error: unsupported agent '${agent}'" >&2
      exit 1
      ;;
  esac
}
