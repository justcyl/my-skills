#!/usr/bin/env bash
# alan-run: Execute a run definition (alan/runs/<slug>/run.yaml) in a loop.
#
# Usage:
#   alan-run <slug>                        Run (loops until verifier returns "end")
#   alan-run <slug> --model <model>        Override model
#   alan-run <slug> --thinking <level>     Override thinking level
#   alan-run <slug> --dry-run              Print filled prompt, don't execute
#   alan-run <slug> --status               Show current state and exit
#   alan-run <slug> --note "message"       Add note for next round, then exit
#   alan-run <slug> --window N             Progress lines injected per round (default 10)
#
# Run YAML fields:
#   state:        pending (default) | done | archived
#   context:      Background knowledge injected into every session
#   instruction:  What to do each round
#   verifier:     Evaluation criteria; session must output "verdict: loop|end"
#   model:        (optional) Full model string, e.g. anthropic/claude-opus-4
#   thinking:     (optional) Thinking level

RUNS_DIR="alan/runs"
MODEL=""
THINKING=""
DRY_RUN=false
STATUS_ONLY=false
NOTE_MSG=""
PROGRESS_WINDOW=10
SLUG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)      MODEL="$2";           shift 2 ;;
    --thinking)   THINKING="$2";        shift 2 ;;
    --dry-run)    DRY_RUN=true;         shift   ;;
    --status)     STATUS_ONLY=true;     shift   ;;
    --note)       NOTE_MSG="$2";        shift 2 ;;
    --window)     PROGRESS_WINDOW="$2"; shift 2 ;;
    --help|-h)    sed -n '2,18p' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*)           echo "Unknown flag: $1" >&2; exit 1 ;;
    *)            SLUG="$1"; shift ;;
  esac
done

if [[ -z "$SLUG" ]]; then
  echo "Usage: alan-run <slug> [options]" >&2
  exit 1
fi

RUN_DIR="${RUNS_DIR}/${SLUG}"
RUN_FILE="${RUN_DIR}/run.yaml"
PROGRESS_FILE="${RUN_DIR}/progress.md"
NOTES_FILE="${RUN_DIR}/notes"

# ── Helpers ──────────────────────────────────────────────────────────

die() { echo "ERROR: $*" >&2; exit 1; }

ensure_run_exists() {
  [[ -f "$RUN_FILE" ]] || die "Run not found: $RUN_FILE"
}

yq_field() {
  yq -r ".$1 // \"\"" "$RUN_FILE"
}

# Derive current round from rows already in progress.md
get_round() {
  if [[ ! -f "$PROGRESS_FILE" ]]; then echo 0; return; fi
  local count
  count=$(grep -c '^| [0-9]' "$PROGRESS_FILE" 2>/dev/null) || count=0
  echo "$count"
}

init_progress() {
  if [[ ! -f "$PROGRESS_FILE" ]]; then
    printf '# Progress\n\n| Round | Verdict | Summary |\n|-------|---------|----------|\n' \
      > "$PROGRESS_FILE"
  fi
}

append_progress() {
  printf '| %s | %s | %s |\n' "$1" "$2" "$3" >> "$PROGRESS_FILE"
}

progress_tail() {
  if [[ -f "$PROGRESS_FILE" ]]; then
    head -3 "$PROGRESS_FILE"
    tail -n +"4" "$PROGRESS_FILE" | tail -n "$PROGRESS_WINDOW"
  else
    echo "(no progress yet)"
  fi
}

load_notes() {
  if [[ -f "$NOTES_FILE" && -s "$NOTES_FILE" ]]; then cat "$NOTES_FILE"; else echo "(none)"; fi
}

clear_notes() {
  [[ -f "$NOTES_FILE" ]] && : > "$NOTES_FILE"
}

build_prompt() {
  local ctx instr verif prog notes
  ctx="$(yq_field context)"
  instr="$(yq_field instruction)"
  verif="$(yq_field verifier)"
  prog="$(progress_tail)"
  notes="$(load_notes)"

  cat <<PROMPT
## Context
${ctx}

## Round
${ROUND}

## Progress So Far
${prog}

## User Notes
${notes}

## Instruction
${instr}

## Before You Finish — Verifier
${verif}

You MUST end your response with this exact block:
\`\`\`result
verdict: loop | end
summary: <one line describing what happened this round>
\`\`\`
PROMPT
}

parse_verdict() {
  printf '%s' "$1" | awk '/^```result/{f=1;next} f && /^verdict:/{print; exit} /^```/{f=0}' \
    | sed 's/^verdict:[[:space:]]*//' | tr -d '[:space:]'
}

parse_summary() {
  printf '%s' "$1" | awk '/^```result/{f=1;next} f && /^summary:/{sub(/^summary:[[:space:]]*/,""); print; exit} /^```/{f=0}'
}

resolve_model_args() {
  local args=()
  local m="$MODEL"
  local t="$THINKING"
  [[ -z "$m" ]] && m="$(yq_field model)"
  [[ -z "$t" ]] && t="$(yq_field thinking)"
  [[ -n "$m" ]] && args+=(--model "$m")
  [[ -n "$t" ]] && args+=(--thinking "$t")
  printf '%s\n' "${args[@]}"
}

# ── Commands ─────────────────────────────────────────────────────────

# --note
if [[ -n "$NOTE_MSG" ]]; then
  ensure_run_exists
  printf -- '- %s\n' "$NOTE_MSG" >> "$NOTES_FILE"
  echo "Note added to $RUN_DIR/notes"
  exit 0
fi

# --status
if [[ "$STATUS_ONLY" == true ]]; then
  ensure_run_exists
  run_state="$(yq_field state)"
  round="$(get_round)"
  echo "Run:    $SLUG"
  echo "State:  ${run_state:-pending}"
  echo "Round:  $round"
  echo ""
  progress_tail
  echo ""
  if [[ -f "$NOTES_FILE" && -s "$NOTES_FILE" ]]; then
    echo "Pending notes:"; cat "$NOTES_FILE"
  fi
  exit 0
fi

# ── Main loop ─────────────────────────────────────────────────────────

ensure_run_exists
mkdir -p "$RUN_DIR"
init_progress

# Check lifecycle state
run_state="$(yq_field state)"
if [[ "$run_state" == "archived" ]]; then
  echo "Run '$SLUG' is archived. Set state: pending in $RUN_FILE to reactivate."
  exit 1
fi
if [[ "$run_state" == "done" ]]; then
  echo "Run '$SLUG' is already done. Set state: pending in $RUN_FILE to re-run."
  exit 0
fi

ROUND=$(get_round)

printf '\n%s\n  alan-run: %s\n%s\n\n' \
  "═══════════════════════════════════════════" \
  "$SLUG" \
  "═══════════════════════════════════════════"

while true; do
  ROUND=$((ROUND + 1))

  printf '── Round %s ──────────────────────────\n' "$ROUND"

  prompt="$(build_prompt)"

  # Dry run
  if [[ "$DRY_RUN" == true ]]; then
    printf '%s\n' "$prompt"
    exit 0
  fi

  round_log="${RUN_DIR}/round-$(printf '%03d' "$ROUND").log"
  echo "  Running session..."
  echo "  Log -> ${round_log}"

  mapfile -t extra_args < <(resolve_model_args)

  pi --print \
    --no-session \
    --no-skills \
    --no-context-files \
    "${extra_args[@]}" \
    "$prompt" > "$round_log" 2>&1

  pi_exit=$?
  output=""
  [[ -f "$round_log" ]] && output="$(cat "$round_log")"

  if [[ $pi_exit -ne 0 && -z "$output" ]]; then
    echo "  ! Session error (exit $pi_exit), skipping round"
    append_progress "$ROUND" "error" "session failed exit=$pi_exit"
    continue
  fi

  verdict="$(parse_verdict "$output")"
  summary="$(parse_summary "$output")"

  if [[ -z "$verdict" ]]; then
    echo "  ! No verdict parsed; treating as loop"
    verdict="loop"
    summary="(no structured output)"
  fi

  append_progress "$ROUND" "$verdict" "$summary"
  clear_notes

  echo "  Verdict: $verdict"
  echo "  Summary: $summary"
  echo ""

  if [[ "$verdict" == "end" ]]; then
    yq -i '.state = "done"' "$RUN_FILE"
    printf '%s\n  Completed after %s rounds.\n%s\n\n' \
      "═══════════════════════════════════════════" \
      "$ROUND" \
      "═══════════════════════════════════════════"
    break
  fi

done
