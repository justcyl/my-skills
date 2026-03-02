#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

usage() {
  cat >&2 <<'TEXT'
usage:
  bash scripts/distribute_skills.sh sync [--agent <codex|claude-code|all>] [--skill-id <id>] [--mode <auto|symlink|copy>] [--dry-run]
  bash scripts/distribute_skills.sh status [--agent <codex|claude-code|all>] [--skill-id <id>]
TEXT
}

copy_skill_dir() {
  local source_path="$1"
  local target_path="$2"
  rm -rf "${target_path}"
  mkdir -p "${target_path}"
  cp -R "${source_path}/." "${target_path}/"
}

upsert_agent_state() {
  local agent="$1"
  local skill_id="$2"
  local source_path="$3"
  local target_path="$4"
  local mode="$5"
  local sync_status="$6"
  local state_path="${AGENTS_DIR}/${agent}.json"
  local temp_file

  temp_file="$(mktemp)"
  jq \
    --arg agent "${agent}" \
    --arg skill_id "${skill_id}" \
    --arg source_path "${source_path}" \
    --arg target_path "${target_path}" \
    --arg mode "${mode}" \
    --arg sync_status "${sync_status}" \
    --arg timestamp "${TIMESTAMP}" \
    '.agent = $agent | .skills[$skill_id] = {
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

sync_one() {
  local agent="$1"
  local skill_id="$2"
  local mode="$3"
  local dry_run="$4"
  local source_path target_base target_path effective_mode

  source_path="$(skill_root_path "${skill_id}")"
  if [[ ! -d "${source_path}" ]]; then
    echo "warning: missing skill directory for ${skill_id}, skipping" >&2
    return
  fi

  target_base="$(resolve_agent_target_dir "${agent}")"
  target_path="${target_base}/${skill_id}"

  if [[ "${dry_run}" -eq 1 ]]; then
    echo "agent=${agent} skill=${skill_id} source=${source_path} target=${target_path} mode=${mode}"
    return
  fi

  mkdir -p "${target_base}"
  effective_mode="${mode}"
  if [[ "${mode}" == "auto" ]]; then
    effective_mode="symlink"
  fi

  if [[ "${effective_mode}" == "copy" ]]; then
    copy_skill_dir "${source_path}" "${target_path}"
    effective_mode="copy"
  else
    rm -rf "${target_path}"
    if ln -s "${source_path}" "${target_path}" 2>/dev/null; then
      effective_mode="symlink"
    elif [[ "${mode}" == "symlink" ]]; then
      echo "error: failed to create symlink for ${skill_id} -> ${agent}" >&2
      return 1
    else
      copy_skill_dir "${source_path}" "${target_path}"
      effective_mode="copy"
    fi
  fi

  upsert_agent_state "${agent}" "${skill_id}" "${skill_id}" "${target_path}" "${effective_mode}" synced
  upsert_registry_distribution "${agent}" "${skill_id}" "${target_path}" "${effective_mode}" synced
}

command_sync() {
  local target_agent="all"
  local skill_id=""
  local mode="auto"
  local dry_run=0

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --agent)
        target_agent="${2:-}"
        shift 2
        ;;
      --skill-id)
        skill_id="${2:-}"
        shift 2
        ;;
      --mode)
        mode="${2:-}"
        shift 2
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

  case "${target_agent}" in
    all) agents=(codex claude-code) ;;
    codex|claude-code) agents=("${target_agent}") ;;
    *) echo "error: invalid agent '${target_agent}'" >&2; exit 1 ;;
  esac

  case "${mode}" in
    auto|symlink|copy) ;;
    *) echo "error: invalid mode '${mode}'" >&2; exit 1 ;;
  esac

  if [[ -n "${skill_id}" ]]; then
    skill_ids=("${skill_id}")
  else
    mapfile -t skill_ids < <(list_skill_ids)
  fi

  for agent in "${agents[@]}"; do
    for current_skill_id in "${skill_ids[@]}"; do
      sync_one "${agent}" "${current_skill_id}" "${mode}" "${dry_run}"
    done
  done

  echo "repo_root=${REPO_ROOT}"
  echo "target_agent=${target_agent}"
  echo "skill_filter=${skill_id:-all}"
  echo "mode=${mode}"
  echo "dry_run=${dry_run}"
}

command_status() {
  local target_agent="all"
  local skill_id=""

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --agent)
        target_agent="${2:-}"
        shift 2
        ;;
      --skill-id)
        skill_id="${2:-}"
        shift 2
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

  case "${target_agent}" in
    all) agents=(codex claude-code) ;;
    codex|claude-code) agents=("${target_agent}") ;;
    *) echo "error: invalid agent '${target_agent}'" >&2; exit 1 ;;
  esac

  for agent in "${agents[@]}"; do
    if [[ -n "${skill_id}" ]]; then
      jq --arg skill_id "${skill_id}" '.skills[$skill_id] // {}' "${AGENTS_DIR}/${agent}.json"
    else
      jq '.' "${AGENTS_DIR}/${agent}.json"
    fi
  done
}

subcommand="${1:-sync}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "${subcommand}" in
  sync)
    command_sync "$@"
    ;;
  status)
    command_status "$@"
    ;;
  *)
    usage
    exit 1
    ;;
esac
