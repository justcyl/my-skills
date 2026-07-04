#!/usr/bin/env bash
# 无头浏览器逐页截图 HTML deck，用于检查溢出与对齐。
#
# 用法：
#   bash screenshot.sh <deck.html> [页码...]
#   页码缺省时截第 1 页。输出到 deck 同目录的 shots/ 下。
#
# 依赖：本机任一 Chromium 系浏览器（Chrome / Edge / Brave / Arc / Chromium）。
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: bash screenshot.sh <deck.html> [页码...]" >&2
  exit 1
fi

deck="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
shift
pages=("${@:-1}")

# 按常见程度探测可用的 Chromium 系浏览器
browser=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  "/Applications/Arc.app/Contents/MacOS/Arc" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v chromium || true)" \
  "$(command -v google-chrome || true)"; do
  if [[ -n "$c" && -x "$c" ]]; then browser="$c"; break; fi
done
if [[ -z "$browser" ]]; then
  echo "error: 未找到 Chromium 系浏览器" >&2
  exit 1
fi

outdir="$(dirname "$deck")/shots"
mkdir -p "$outdir"

for p in "${pages[@]}"; do
  out="$outdir/slide-$(printf '%02d' "$p").png"
  "$browser" --headless --disable-gpu --hide-scrollbars \
    --screenshot="$out" --window-size=1280,720 \
    "file://$deck#$p" >/dev/null 2>&1
  echo "$out"
done
