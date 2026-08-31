#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: download_hjfy_pdf.sh --input <hjfy-url|arxiv-url|arxiv-id> [options]

Options:
  --output-dir <dir>  Destination directory (default: current directory)
  --name <filename>   Output filename (default: <id>_zh_CN.pdf)
  --force             Replace an existing output file
  -h, --help          Show this help
EOF
}

input=""
output_dir="."
output_name=""
force=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --input)
      input="${2:-}"
      shift 2
      ;;
    --output-dir)
      output_dir="${2:-}"
      shift 2
      ;;
    --name)
      output_name="${2:-}"
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$input" ]]; then
  usage
  exit 2
fi

for command_name in curl jq; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "error: required command not found: $command_name" >&2
    exit 1
  fi
done

source_value="${input%%#*}"
source_value="${source_value%%\?*}"
source_value="${source_value%/}"
arxiv_id="$source_value"

if [[ "$source_value" =~ ^https?://([^/]+\.)?hjfy\.top/arxiv/(.+)$ ]]; then
  arxiv_id="${BASH_REMATCH[2]}"
elif [[ "$source_value" =~ ^https?://([^/]+\.)?arxiv\.org/(abs|pdf)/(.+)$ ]]; then
  arxiv_id="${BASH_REMATCH[3]}"
fi

arxiv_id="${arxiv_id%.pdf}"
arxiv_id="${arxiv_id%/}"
api_id="${arxiv_id//\//_}"

if [[ ! "$api_id" =~ ^[0-9]{4}\.[0-9]{4,}(v[0-9]+)?$ && \
      ! "$api_id" =~ ^[A-Za-z.-]+_[0-9]+(v[0-9]+)?$ ]]; then
  echo "error: unsupported arXiv identifier: $arxiv_id" >&2
  exit 2
fi

api_base="${HJFY_API_BASE:-https://hjfy.top/api}"
status_json="$(curl --fail --silent --show-error --location \
  --retry 3 --retry-delay 1 --retry-all-errors \
  "$api_base/arxivStatus/$api_id")"

if [[ "$(printf '%s' "$status_json" | jq -r '.status // empty')" != "0" ]]; then
  message="$(printf '%s' "$status_json" | jq -r '.msg // "unknown HJFY API error"')"
  echo "error: HJFY status request failed: $message" >&2
  exit 1
fi

translation_status="$(printf '%s' "$status_json" | jq -r '.data.status // empty')"
if [[ "$translation_status" != "finished" ]]; then
  echo "error: HJFY translation is not finished (status: ${translation_status:-unknown})" >&2
  exit 3
fi

files_json="$(curl --fail --silent --show-error --location \
  --retry 3 --retry-delay 1 --retry-all-errors \
  "$api_base/arxivFiles/$api_id")"

if [[ "$(printf '%s' "$files_json" | jq -r '.status // empty')" != "0" ]]; then
  message="$(printf '%s' "$files_json" | jq -r '.msg // "unknown HJFY API error"')"
  echo "error: HJFY files request failed: $message" >&2
  exit 1
fi

pdf_url="$(printf '%s' "$files_json" | jq -r '.data.zhCN // empty')"
title="$(printf '%s' "$files_json" | jq -r '.data.title // empty')"
if [[ -z "$pdf_url" ]]; then
  echo "error: translated PDF URL is missing" >&2
  exit 4
fi

if [[ -z "$output_name" ]]; then
  output_name="${api_id}_zh_CN.pdf"
fi
if [[ "$output_name" == */* || "$output_name" == *$'\n'* || "$output_name" == *$'\r'* ]]; then
  echo "error: --name must be a plain filename" >&2
  exit 2
fi
if [[ "$output_name" != *.pdf ]]; then
  echo "error: output filename must end in .pdf" >&2
  exit 2
fi

mkdir -p "$output_dir"
output_path="$output_dir/$output_name"
if [[ -e "$output_path" && "$force" -ne 1 ]]; then
  echo "error: output file already exists: $output_path" >&2
  exit 5
fi

temp_path="$(mktemp "$output_path.part.XXXXXX")"
cleanup() {
  rm -f "$temp_path"
}
trap cleanup EXIT

# Fetch immediately because HJFY returns a short-lived signed object URL.
curl --fail --silent --show-error --location \
  --retry 2 --retry-delay 1 --retry-all-errors \
  --output "$temp_path" "$pdf_url"

if [[ "$(head -c 5 "$temp_path")" != "%PDF-" ]]; then
  echo "error: downloaded content is not a PDF" >&2
  exit 6
fi

mv -f "$temp_path" "$output_path"
trap - EXIT
bytes="$(wc -c < "$output_path" | tr -d '[:space:]')"
absolute_path="$(cd "$(dirname "$output_path")" && pwd)/$(basename "$output_path")"

jq -n \
  --arg arxiv_id "$arxiv_id" \
  --arg api_id "$api_id" \
  --arg title "$title" \
  --arg path "$absolute_path" \
  --argjson bytes "$bytes" \
  '{arxiv_id: $arxiv_id, api_id: $api_id, title: $title, path: $path, bytes: $bytes}'
