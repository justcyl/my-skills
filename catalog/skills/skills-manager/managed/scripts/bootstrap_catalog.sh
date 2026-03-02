#!/usr/bin/env bash
set -euo pipefail

# 解析当前脚本所在 skill 的根目录，再回到仓库根目录。
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

write_source_json() {
  local skill_id="$1"
  local display_name="$2"
  local managed_revision="$3"

  jq -n \
    --arg skill_id "${skill_id}" \
    --arg display_name "${display_name}" \
    --arg managed_revision "${managed_revision}" \
    --arg timestamp "${TIMESTAMP}" \
    '{
      skill_id: $skill_id,
      display_name: $display_name,
      source_type: "local-bootstrap",
      source: "",
      source_url: "",
      ref: "",
      subpath: "",
      bootstrap: true,
      upstream_enabled: false,
      last_imported_at: $timestamp,
      upstream_revision: "",
      managed_revision: $managed_revision,
      managed_dirty: false
    }' > "${SOURCES_DIR}/${skill_id}.json"
}

write_report_md() {
  local skill_id="$1"
  local display_name="$2"
  local description="$3"

  cat > "${REPORTS_DIR}/${skill_id}.md" <<EOF
# ${display_name}

- skill_id: \`${skill_id}\`
- status: bootstrapped
- source_type: \`local-bootstrap\`
- upstream_enabled: \`false\`
- managed_path: \`catalog/skills/${skill_id}/managed\`

## Summary

${description:-No description found in frontmatter.}

## Notes

- This skill was registered from the current repository as part of the initial bootstrap.
- No upstream source is configured yet.
- Future updates require either manual edits in \`managed/\` or explicit source registration.
EOF
}

update_registry_entry() {
  local skill_id="$1"
  local display_name="$2"
  local description="$3"
  local managed_revision="$4"

  local temp_file
  temp_file="$(mktemp)"

  jq \
    --arg skill_id "${skill_id}" \
    --arg display_name "${display_name}" \
    --arg description "${description}" \
    --arg managed_revision "${managed_revision}" \
    --arg timestamp "${TIMESTAMP}" \
    '.skills[$skill_id] = {
      display_name: $display_name,
      description: $description,
      status: "bootstrapped",
      audit_status: "pending",
      managed_dirty: false,
      has_upstream: false,
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

mkdir -p "${SKILLS_DIR}" "${SOURCES_DIR}" "${REPORTS_DIR}" "${LOCKS_DIR}"

if [[ ! -f "${REGISTRY_PATH}" ]]; then
  cat > "${REGISTRY_PATH}" <<'EOF'
{
  "version": 1,
  "skills": {}
}
EOF
fi

bootstrapped_count=0

for candidate_dir in "${REPO_ROOT}"/*; do
  [[ -d "${candidate_dir}" ]] || continue

  candidate_name="$(basename "${candidate_dir}")"

  case "${candidate_name}" in
    .git|catalog|docs)
      continue
      ;;
  esac

  skill_md_path="${candidate_dir}/SKILL.md"
  [[ -f "${skill_md_path}" ]] || continue

  skill_id="$(sanitize_skill_id "${candidate_name}")"
  [[ -n "${skill_id}" ]] || continue

  display_name="$(extract_frontmatter_value "${skill_md_path}" "name")"
  description="$(extract_frontmatter_value "${skill_md_path}" "description")"

  if [[ -z "${display_name}" ]]; then
    display_name="${skill_id}"
  fi

  destination_root="${SKILLS_DIR}/${skill_id}"
  managed_dir="${destination_root}/managed"
  upstream_dir="${destination_root}/upstream"

  rm -rf "${destination_root}"
  mkdir -p "${managed_dir}" "${upstream_dir}"
  cp -R "${candidate_dir}/." "${managed_dir}/"

  managed_revision="$(compute_directory_hash "${managed_dir}")"

  write_source_json "${skill_id}" "${display_name}" "${managed_revision}"
  write_report_md "${skill_id}" "${display_name}" "${description}"
  update_registry_entry "${skill_id}" "${display_name}" "${description}" "${managed_revision}"

  bootstrapped_count="$((bootstrapped_count + 1))"
  echo "bootstrapped ${skill_id}"
done

echo "repo_root=${REPO_ROOT}"
echo "bootstrapped_count=${bootstrapped_count}"
echo "registry=${REGISTRY_PATH}"
