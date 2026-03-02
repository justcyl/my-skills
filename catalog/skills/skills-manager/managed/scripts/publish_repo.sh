#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/.." && pwd)"

COMMIT_MESSAGE=""
PUSH_AFTER_COMMIT=0
DRY_RUN=0

usage() {
  cat >&2 <<'EOF'
usage: bash skills-manager/scripts/publish_repo.sh [--message <msg>] [--push] [--dry-run]
EOF
}

generate_default_message() {
  local summary

  summary="$(git -C "${REPO_ROOT}" status --porcelain | awk '
    {
      path = $2
      sub(/^"/, "", path)
      sub(/"$/, "", path)
      split(path, parts, "/")
      print parts[1]
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
      COMMIT_MESSAGE="${2:-}"
      shift 2
      ;;
    --push)
      PUSH_AFTER_COMMIT=1
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

cd "${REPO_ROOT}"

BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
STATUS_OUTPUT="$(git status --short)"

if [[ -z "${COMMIT_MESSAGE}" ]]; then
  COMMIT_MESSAGE="$(generate_default_message)"
fi

if [[ -z "${STATUS_OUTPUT}" ]]; then
  echo "publish_repo.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "branch=${BRANCH_NAME}"
  echo "status=clean"
  exit 0
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "publish_repo.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "branch=${BRANCH_NAME}"
  echo "commit_message=${COMMIT_MESSAGE}"
  echo "push_after_commit=${PUSH_AFTER_COMMIT}"
  printf '%s\n' "${STATUS_OUTPUT}"
  exit 0
fi

git add -A

if git diff --cached --quiet; then
  echo "publish_repo.sh"
  echo "repo_root=${REPO_ROOT}"
  echo "branch=${BRANCH_NAME}"
  echo "status=no-staged-changes"
  exit 0
fi

git commit -m "${COMMIT_MESSAGE}"

if [[ "${PUSH_AFTER_COMMIT}" -eq 1 ]]; then
  git push origin "${BRANCH_NAME}"
fi

echo "publish_repo.sh"
echo "repo_root=${REPO_ROOT}"
echo "branch=${BRANCH_NAME}"
echo "commit_message=${COMMIT_MESSAGE}"
echo "push_after_commit=${PUSH_AFTER_COMMIT}"
