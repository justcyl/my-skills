#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"
CATALOG_DIR="${REPO_ROOT}/catalog"
SKILLS_DIR="${CATALOG_DIR}/skills"
AGENTS_STATE_DIR="${CATALOG_DIR}/agents"
LOCKS_DIR="${CATALOG_DIR}/locks"
REGISTRY_PATH="${LOCKS_DIR}/registry.json"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

TARGET_AGENT="all"
TARGET_SKILL_ID=""
SYNC_MODE="auto"
DRY_RUN=0

usage() {
  cat >&2 <<'EOF'
usage: bash skills-manager/scripts/sync_agents.sh [--agent <codex|claude-code|all>] [--skill-id <id>] [--mode <auto|symlink|copy>] [--dry-run]
EOF
}

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required" >&2
  exit 1
fi

if [[ ! -f "${REGISTRY_PATH}" ]]; then
  echo "error: registry not found at ${REGISTRY_PATH}" >&2
  exit 1
fi

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

upsert_agent_state() {
  local agent="$1"
  local skill_id="$2"
  local source_path="$3"
  local target_path="$4"
  local mode="$5"
  local sync_status="$6"
  local state_path="${AGENTS_STATE_DIR}/${agent}.json"
  local temp_file

  temp_file="$(mktemp)"

  jq \
    --arg skill_id "${skill_id}" \
    --arg source_path "${source_path}" \
    --arg target_path "${target_path}" \
    --arg mode "${mode}" \
    --arg sync_status "${sync_status}" \
    --arg timestamp "${TIMESTAMP}" \
    '.skills[$skill_id] = {
      source_path: $source_path,
      target_path: $target_path,
      mode: $mode,
      sync_status: $sync_status,
      last_synced_at: $timestamp
    }' "${state_path}" > "${temp_file}"

  mv "${temp_file}" "${state_path}"
}

upsert_registry_distribution() {
  local agent="$1"
  local skill_id="$2"
  local target_path="$3"
  local mode="$4"
  local sync_status="$5"
  local temp_file

  temp_file="$(mktemp)"

  jq \
    --arg skill_id "${skill_id}" \
    --arg agent "${agent}" \
    --arg target_path "${target_path}" \
    --arg mode "${mode}" \
    --arg sync_status "${sync_status}" \
    --arg timestamp "${TIMESTAMP}" \
    '.skills[$skill_id].distribution[$agent] = {
      target_path: $target_path,
      mode: $mode,
      sync_status: $sync_status,
      last_synced_at: $timestamp
    }' "${REGISTRY_PATH}" > "${temp_file}"

  mv "${temp_file}" "${REGISTRY_PATH}"
}

copy_skill_dir() {
  local source_path="$1"
  local target_path="$2"

  rm -rf "${target_path}"
  mkdir -p "${target_path}"
  cp -R "${source_path}/." "${target_path}/"
}

create_symlink_or_fallback() {
  local source_path="$1"
  local target_path="$2"
  local preferred_mode="$3"
  local result_mode=""

  mkdir -p "$(dirname "${target_path}")"

  if [[ "${preferred_mode}" == "copy" ]]; then
    copy_skill_dir "${source_path}" "${target_path}"
    printf 'copy\n'
    return
  fi

  rm -rf "${target_path}"

  if ln -s "${source_path}" "${target_path}" 2>/dev/null; then
    printf 'symlink\n'
    return
  fi

  if [[ "${preferred_mode}" == "symlink" ]]; then
    echo "error"
    return 1
  fi

  copy_skill_dir "${source_path}" "${target_path}"
  printf 'copy\n'
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --agent)
      TARGET_AGENT="${2:-}"
      shift 2
      ;;
    --skill-id)
      TARGET_SKILL_ID="${2:-}"
      shift 2
      ;;
    --mode)
      SYNC_MODE="${2:-}"
      shift 2
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

case "${SYNC_MODE}" in
  auto|symlink|copy)
    ;;
  *)
    echo "error: invalid mode '${SYNC_MODE}'" >&2
    exit 1
    ;;
esac

case "${TARGET_AGENT}" in
  all)
    AGENTS=("codex" "claude-code")
    ;;
  codex|claude-code)
    AGENTS=("${TARGET_AGENT}")
    ;;
  *)
    echo "error: invalid agent '${TARGET_AGENT}'" >&2
    exit 1
    ;;
esac

if [[ -n "${TARGET_SKILL_ID}" ]]; then
  SKILL_IDS=("${TARGET_SKILL_ID}")
else
  mapfile -t SKILL_IDS < <(jq -r '.skills | keys[]' "${REGISTRY_PATH}" | LC_ALL=C sort)
fi

if [[ "${#SKILL_IDS[@]}" -eq 0 ]]; then
  echo "error: no skills available to sync" >&2
  exit 1
fi

synced_count=0

for agent in "${AGENTS[@]}"; do
  target_base="$(resolve_agent_target_dir "${agent}")"
  mkdir -p "${target_base}"

  for skill_id in "${SKILL_IDS[@]}"; do
    source_path="${SKILLS_DIR}/${skill_id}/managed"

    if [[ ! -d "${source_path}" ]]; then
      echo "warning: missing managed path for ${skill_id}, skipping" >&2
      continue
    fi

    target_path="${target_base}/${skill_id}"

    if [[ "${DRY_RUN}" -eq 1 ]]; then
      echo "agent=${agent} skill=${skill_id} source=${source_path} target=${target_path} mode=${SYNC_MODE}"
      continue
    fi

    actual_mode="$(create_symlink_or_fallback "${source_path}" "${target_path}" "${SYNC_MODE}")"
    upsert_agent_state "${agent}" "${skill_id}" "${source_path}" "${target_path}" "${actual_mode}" "ok"
    upsert_registry_distribution "${agent}" "${skill_id}" "${target_path}" "${actual_mode}" "ok"
    synced_count="$((synced_count + 1))"
    echo "synced ${skill_id} -> ${agent} (${actual_mode})"
  done
done

echo "repo_root=${REPO_ROOT}"
echo "target_agent=${TARGET_AGENT}"
echo "skill_filter=${TARGET_SKILL_ID:-all}"
echo "mode=${SYNC_MODE}"
echo "dry_run=${DRY_RUN}"
echo "synced_count=${synced_count}"
