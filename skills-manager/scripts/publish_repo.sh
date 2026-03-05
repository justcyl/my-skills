#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

commit_message=""
push_after_commit=0
dry_run=0

usage() {
  cat >&2 <<'TEXT'
usage: bash scripts/publish_repo.sh [--message <msg>] [--push] [--dry-run]
TEXT
}

generate_default_message() {
  local summary

  summary="$(git -C "${REPO_ROOT}" status --porcelain | awk '
    {
      path = $2
      sub(/^"/, "", path)
      sub(/"$/, "", path)
      split(path, parts, "/")
      top = parts[1]
      if (top == ".skills" || top == "catalog") {
        top = "skill-state"
      }
      print top
    }
  ' | LC_ALL=C sort -u | tr '\n' ' ')"

  if [[ -z "${summary// }" ]]; then
    printf 'Update skills repository\n'
    return
  fi

  printf 'Update %s\n' "${summary%% }"
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --message)
      commit_message="${2:-}"
      shift 2
      ;;
    --push)
      push_after_commit=1
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

cd "${REPO_ROOT}"
branch_name="$(git rev-parse --abbrev-ref HEAD)"
status_output="$(git status --short)"

if [[ -z "${commit_message}" ]]; then
  commit_message="$(generate_default_message)"
fi

if [[ -z "${status_output}" ]]; then
  echo "publish_repo.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "branch=${branch_name}"
  echo "status=clean"
  exit 0
fi

if [[ "${dry_run}" -eq 1 ]]; then
  echo "publish_repo.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "branch=${branch_name}"
  echo "commit_message=${commit_message}"
  echo "push_after_commit=${push_after_commit}"
  printf '%s\n' "${status_output}"
  exit 0
fi

git add -A
if git diff --cached --quiet; then
  echo "publish_repo.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "branch=${branch_name}"
  echo "status=no-staged-changes"
  exit 0
fi

git commit -m "${commit_message}"
if [[ "${push_after_commit}" -eq 1 ]]; then
  git push origin "${branch_name}"
fi

echo "publish_repo.sh"
echo "repo_root=${REPO_ROOT}"
echo "branch=${branch_name}"
echo "commit_message=${commit_message}"
echo "push_after_commit=${push_after_commit}"
