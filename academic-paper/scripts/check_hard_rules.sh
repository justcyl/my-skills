#!/usr/bin/env bash
# check_hard_rules.sh — Hard-rule format checker for academic paper submissions
#
# Usage:
#   bash check_hard_rules.sh <pdf_path> <conference> <type> [OPTIONS]
#
# Arguments:
#   pdf_path    Path to compiled PDF
#   conference  neurips | icml | iclr | acl | emnlp | aaai
#   type        submission | camera-ready
#
# Options:
#   --paper-type <long|short>   ACL/EMNLP paper type (default: long)
#   --log <path>                LaTeX .log file for compile-error checks
#   --no-blind                  Skip anonymity checks (not applicable to double-blind)
#
# Dependencies: pdfinfo, pdffonts, pdftotext  (brew install poppler)

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

PASS="${GREEN}✅ PASS${RESET}"
WARN="${YELLOW}⚠️  WARN${RESET}"
FAIL="${RED}❌ FAIL${RESET}"

pass_count=0; warn_count=0; fail_count=0
results=()  # stores "LEVEL|label|detail"

record() {
  local level="$1" label="$2" detail="$3"
  results+=("${level}|${label}|${detail}")
  case "$level" in
    PASS) ((pass_count++)) ;;
    WARN) ((warn_count++)) ;;
    FAIL) ((fail_count++)) ;;
  esac
}

# ── Argument parsing ──────────────────────────────────────────────────────────
if [[ $# -lt 3 ]]; then
  echo "Usage: bash check_hard_rules.sh <pdf_path> <conference> <submission|camera-ready> [OPTIONS]"
  echo "Conferences: neurips | icml | iclr | acl | emnlp | aaai"
  exit 2
fi

PDF="$1"; CONF="${2,,}"; TYPE="${3,,}"
PAPER_TYPE="long"; LOG_FILE=""; BLIND=true

shift 3
while [[ $# -gt 0 ]]; do
  case "$1" in
    --paper-type) PAPER_TYPE="${2,,}"; shift 2 ;;
    --log)        LOG_FILE="$2";       shift 2 ;;
    --no-blind)   BLIND=false;         shift   ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

# ── Dependency check ──────────────────────────────────────────────────────────
missing_deps=()
for cmd in pdfinfo pdffonts pdftotext; do
  command -v "$cmd" &>/dev/null || missing_deps+=("$cmd")
done
if [[ ${#missing_deps[@]} -gt 0 ]]; then
  echo -e "${RED}Missing dependencies: ${missing_deps[*]}${RESET}"
  echo "Install: brew install poppler   or   apt-get install poppler-utils"
  exit 1
fi

if [[ ! -f "$PDF" ]]; then
  echo -e "${RED}PDF not found: $PDF${RESET}"; exit 1
fi

# ── Extract text once ─────────────────────────────────────────────────────────
TMP_TEXT=$(mktemp /tmp/check_paper_XXXXXX.txt)
trap 'rm -f "$TMP_TEXT"' EXIT
pdftotext "$PDF" "$TMP_TEXT" 2>/dev/null || true

echo -e "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  Academic Paper Hard-Rule Checker${RESET}"
echo -e "${BOLD}  PDF:        ${RESET}$PDF"
echo -e "${BOLD}  Conference: ${RESET}${CONF^^}  |  Type: $TYPE  |  Paper: $PAPER_TYPE"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

# ═════════════════════════════════════════════════════
# H1  Paper size = US Letter (612 × 792 pts)
# ═════════════════════════════════════════════════════
size_line=$(pdfinfo "$PDF" 2>/dev/null | grep -i "Page size" | head -1 || true)
if echo "$size_line" | grep -qE "612(\.[0-9]+)? x 792(\.[0-9]+)?"; then
  record PASS "H1 Paper size" "US Letter (612 × 792 pts) ✓"
else
  actual=$(echo "$size_line" | sed 's/Page size://;s/pts//g;s/^ *//' || echo "unknown")
  record FAIL "H1 Paper size" "Expected 612 × 792 pts (US Letter), got: $actual"
fi

# ═════════════════════════════════════════════════════
# H2  PDF file size < 50 MB
# ═════════════════════════════════════════════════════
file_bytes=$(stat -f%z "$PDF" 2>/dev/null || stat -c%s "$PDF" 2>/dev/null || echo 0)
file_mb=$(echo "scale=1; $file_bytes / 1048576" | bc)
if (( file_bytes < 52428800 )); then  # 50 MB
  record PASS "H2 File size" "${file_mb} MB (< 50 MB)"
else
  record FAIL "H2 File size" "${file_mb} MB — exceeds 50 MB limit"
fi

# ═════════════════════════════════════════════════════
# H3  Total page count (informational — no FAIL)
# ═════════════════════════════════════════════════════
total_pages=$(pdfinfo "$PDF" 2>/dev/null | awk '/^Pages:/{print $2}' || echo "?")
# Page limits for reference (body pages only, refs/appendix usually excluded)
case "${CONF}-${TYPE}-${PAPER_TYPE}" in
  neurips-submission-*)      limit="10 body pages (refs excluded)" ;;
  neurips-camera-ready-*)    limit="10 body pages (refs excluded; +1 allowed)" ;;
  icml-submission-*)         limit="8 body pages (refs/impact/appendix excluded)" ;;
  icml-camera-ready-*)       limit="9 body pages" ;;
  iclr-submission-*)         limit="6–10 body pages (refs excluded; min 6)" ;;
  iclr-camera-ready-*)       limit="6–10 body pages" ;;
  acl-submission-long|emnlp-submission-long)  limit="8 body pages (refs/limitations excluded)" ;;
  acl-camera-ready-long|emnlp-camera-ready-long)  limit="9 body pages" ;;
  acl-submission-short|emnlp-submission-short) limit="4 body pages" ;;
  acl-camera-ready-short|emnlp-camera-ready-short) limit="5 body pages" ;;
  aaai-submission-*)         limit="7 body + 2 additional pages (refs INCLUDED in count)" ;;
  aaai-camera-ready-*)       limit="same as submission (refs INCLUDED)" ;;
  *)                         limit="unknown — check conference CFP" ;;
esac
record WARN "H3 Page count" "Total pages in PDF: ${total_pages}. Limit: ${limit}. ⚠️ Script cannot separate body from refs/appendix — verify manually."

# ═════════════════════════════════════════════════════
# H4  Undefined citations [?] in rendered text
# ═════════════════════════════════════════════════════
undef_cites=$(grep -cE '\[\?\]|\[, \]' "$TMP_TEXT" 2>/dev/null || echo 0)
if [[ "$undef_cites" -eq 0 ]]; then
  record PASS "H4 Undefined citations" "No [?] found in rendered text"
else
  record FAIL "H4 Undefined citations" "${undef_cites} occurrence(s) of [?] — unresolved \\cite{}"
fi

# ═════════════════════════════════════════════════════
# H5  Font embedding (camera-ready only)
# ═════════════════════════════════════════════════════
if [[ "$TYPE" == "camera-ready" ]]; then
  unembedded=$(pdffonts "$PDF" 2>/dev/null | tail -n +3 | awk '{print $5}' | grep -c "^no$" || echo 0)
  if [[ "$unembedded" -eq 0 ]]; then
    record PASS "H5 Font embedding" "All fonts embedded"
  else
    font_names=$(pdffonts "$PDF" 2>/dev/null | tail -n +3 | awk '$5=="no"{print $1}' | head -5 | tr '\n' ', ')
    record FAIL "H5 Font embedding" "${unembedded} font(s) not embedded: ${font_names%,}"
  fi
fi

# ═════════════════════════════════════════════════════
# H6  PDF metadata: no Author field (all blind submissions)
# ═════════════════════════════════════════════════════
if [[ "$BLIND" == true && "$TYPE" == "submission" ]]; then
  author_meta=$(pdfinfo "$PDF" 2>/dev/null | grep -i "^Author:" | sed 's/^Author://;s/^ *//' || true)
  if [[ -z "$author_meta" ]]; then
    record PASS "H6 PDF metadata author" "Author field empty or absent"
  else
    record FAIL "H6 PDF metadata author" "PDF metadata contains Author: \"$author_meta\" — remove for blind submission"
  fi
fi

# ═════════════════════════════════════════════════════
# Anonymity checks (blind submissions only)
# ═════════════════════════════════════════════════════
if [[ "$BLIND" == true && "$TYPE" == "submission" ]]; then

  # H7  "our previous/prior/earlier work"
  h7_hits=$(grep -cinE "our (previous|prior|earlier) (work|paper|study|system|approach|method)" "$TMP_TEXT" 2>/dev/null || echo 0)
  if [[ "$h7_hits" -eq 0 ]]; then
    record PASS "H7 Self-reference language" "No 'our previous/prior/earlier work' patterns"
  else
    sample=$(grep -inE "our (previous|prior|earlier) (work|paper|study|system|approach|method)" "$TMP_TEXT" 2>/dev/null | head -2 | tr '\n' '|')
    record FAIL "H7 Self-reference language" "${h7_hits} line(s) — e.g.: ${sample}"
  fi

  # H8  Institutional affiliations in body text
  h8_hits=$(grep -cinE "\buniversity of\b|\binstitute of\b|\blaboratory\b|\bDepartment of\b|\bschool of\b" "$TMP_TEXT" 2>/dev/null || echo 0)
  if [[ "$h8_hits" -eq 0 ]]; then
    record PASS "H8 Institutional names" "No institution names detected in text"
  else
    record WARN "H8 Institutional names" "${h8_hits} line(s) with possible institution names — verify none are author affiliations"
  fi

  # H9  Acknowledgements / funding info
  h9_hits=$(grep -cinE "funded by|supported by|grant (no\.|number|#)|this work was (partially )?supported" "$TMP_TEXT" 2>/dev/null || echo 0)
  if [[ "$h9_hits" -eq 0 ]]; then
    record PASS "H9 Funding acknowledgement" "No funding/acknowledgement patterns found"
  else
    record FAIL "H9 Funding acknowledgement" "${h9_hits} line(s) — acknowledgements section must be removed for blind submission"
  fi

  # H10  Trackable URLs (non-anonymous repos/links)
  h10_hits=$(grep -cinE "https?://(github\.com|gitlab\.com|bitbucket\.org|drive\.google|dropbox\.com)" "$TMP_TEXT" 2>/dev/null || echo 0)
  if [[ "$h10_hits" -eq 0 ]]; then
    record PASS "H10 Trackable URLs" "No trackable repository URLs detected"
  else
    sample=$(grep -inE "https?://(github\.com|gitlab\.com|bitbucket\.org|drive\.google|dropbox\.com)" "$TMP_TEXT" 2>/dev/null | head -2 | tr '\n' '|')
    record WARN "H10 Trackable URLs" "${h10_hits} line(s) with potentially identifiable URLs — use anonymous.4open.science or similar: ${sample}"
  fi

fi  # end blind submission checks

# ═════════════════════════════════════════════════════
# Conference-specific required sections
# ═════════════════════════════════════════════════════
case "$CONF" in
  acl|emnlp)
    # H11  Limitations section (REQUIRED — desk reject if missing)
    if grep -qiE "^[[:space:]]*(\\\\section\{|[0-9]+\.)[[:space:]]*limitation" "$TMP_TEXT" 2>/dev/null ||
       grep -qiE "limitation" "$TMP_TEXT" 2>/dev/null; then
      record PASS "H11 Limitations section" "Limitations section detected"
    else
      record FAIL "H11 Limitations section" "NOT FOUND — required for ${CONF^^}, desk reject risk"
    fi

    # H12  Responsible NLP Checklist / Ethics section
    if grep -qiE "responsible nlp|ethical consideration|broader impact|ethics statement" "$TMP_TEXT" 2>/dev/null; then
      record PASS "H12 Ethics/NLP Checklist" "Ethics-related section detected"
    else
      record WARN "H12 Ethics/NLP Checklist" "No ethics/checklist section found — required for ${CONF^^}"
    fi
    ;;

  icml)
    # H13  Broader Impact / Impact Statement (strongly recommended)
    if grep -qiE "broader impact|impact statement|societal impact" "$TMP_TEXT" 2>/dev/null; then
      record PASS "H13 Impact Statement" "Broader Impact / Impact Statement detected"
    else
      record WARN "H13 Impact Statement" "Not found — strongly recommended for ICML"
    fi
    ;;

  neurips)
    if grep -qiE "broader impact|societal impact|ethical" "$TMP_TEXT" 2>/dev/null; then
      record PASS "H13 Broader Impact" "Broader Impact section detected"
    else
      record WARN "H13 Broader Impact" "Not found — recommended for NeurIPS"
    fi
    ;;
esac

# ═════════════════════════════════════════════════════
# LaTeX log checks (optional, only if --log provided)
# ═════════════════════════════════════════════════════
if [[ -n "$LOG_FILE" ]]; then
  if [[ ! -f "$LOG_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Log file not found: $LOG_FILE — skipping log checks${RESET}"
  else
    # H14  Fatal compile errors
    fatal_count=$(grep -c "^!" "$LOG_FILE" 2>/dev/null || echo 0)
    if [[ "$fatal_count" -eq 0 ]]; then
      record PASS "H14 Fatal errors" "No fatal LaTeX errors (! lines)"
    else
      sample=$(grep "^!" "$LOG_FILE" 2>/dev/null | head -3 | tr '\n' '|')
      record FAIL "H14 Fatal errors" "${fatal_count} fatal error(s): ${sample}"
    fi

    # H15  Undefined citations
    undef_log=$(grep -c "Citation.*undefined\|Reference.*undefined" "$LOG_FILE" 2>/dev/null || echo 0)
    if [[ "$undef_log" -eq 0 ]]; then
      record PASS "H15 Undefined \\cite{}" "No undefined citations in log"
    else
      sample=$(grep "Citation.*undefined\|Reference.*undefined" "$LOG_FILE" 2>/dev/null | head -3 | tr '\n' '|')
      record FAIL "H15 Undefined \\cite{}" "${undef_log} warning(s): ${sample}"
    fi

    # H16  Multiply defined labels
    multi_label=$(grep -c "multiply defined\|has been referenced" "$LOG_FILE" 2>/dev/null || echo 0)
    if [[ "$multi_label" -eq 0 ]]; then
      record PASS "H16 Duplicate labels" "No multiply-defined \\label{} warnings"
    else
      record WARN "H16 Duplicate labels" "${multi_label} multiply-defined label(s)"
    fi

    # H17  Overfull hbox count
    overfull=$(grep -cE "Overfull \\\\hbox" "$LOG_FILE" 2>/dev/null || echo 0)
    if [[ "$overfull" -eq 0 ]]; then
      record PASS "H17 Overfull \\hbox" "No Overfull \\hbox warnings"
    elif [[ "$overfull" -le 5 ]]; then
      record WARN "H17 Overfull \\hbox" "${overfull} warning(s) — minor, review if they cause visible overflow"
    else
      record WARN "H17 Overfull \\hbox" "${overfull} warning(s) — notable, check for text overflow in margins"
    fi
  fi
else
  echo -e "${CYAN}ℹ️  No --log provided. Skipping LaTeX compile-error checks (H14–H17).${RESET}"
  echo -e "${CYAN}   Run with: --log main.log${RESET}\n"
fi

# ═════════════════════════════════════════════════════
# Print results
# ═════════════════════════════════════════════════════
echo -e "\n${BOLD}━━━━━━━━━━ Results ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
for entry in "${results[@]}"; do
  level="${entry%%|*}"; rest="${entry#*|}"
  label="${rest%%|*}"; detail="${rest#*|}"
  case "$level" in
    PASS) icon="$PASS" ;;
    WARN) icon="$WARN" ;;
    FAIL) icon="$FAIL" ;;
  esac
  printf "  %b  %-32s %s\n" "$icon" "$label" "$detail"
done

echo -e "\n${BOLD}━━━━━━━━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  ${GREEN}PASS: $pass_count${RESET}   ${YELLOW}WARN: $warn_count${RESET}   ${RED}FAIL: $fail_count${RESET}"

if [[ "$fail_count" -gt 0 ]]; then
  echo -e "\n  ${RED}${BOLD}❌ $fail_count hard rule(s) failed — fix before submission${RESET}"
  exit 1
elif [[ "$warn_count" -gt 0 ]]; then
  echo -e "\n  ${YELLOW}⚠️  $warn_count warning(s) — review recommended${RESET}"
  exit 0
else
  echo -e "\n  ${GREEN}${BOLD}All hard rules passed.${RESET}"
  exit 0
fi
