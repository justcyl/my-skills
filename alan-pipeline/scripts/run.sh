#!/usr/bin/env bash
# pi-run: Execute a run definition (alan/runs/<slug>.yaml) in a loop.
#
# Usage:
#   pi-run <slug>                         Run (loops until verifier returns "end")
#   pi-run <slug> --model <model>         Override model
#   pi-run <slug> --thinking <level>      Override thinking level
#   pi-run <slug> --dry-run               Print filled prompt, don't execute
#   pi-run <slug> --status                Show current state and exit
#   pi-run <slug> --note "message"        Add note for next round, then exit
#   pi-run <slug> --window N              Progress lines injected per round (default 5)
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
PROGRESS_WINDOW=5
SLUG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)      MODEL="$2";          shift 2 ;;
    --thinking)   THINKING="$2";       shift 2 ;;
    --dry-run)    DRY_RUN=true;        shift   ;;
    --status)     STATUS_ONLY=true;    shift   ;;
    --note)       NOTE_MSG="$2";       shift 2 ;;
    --window)     PROGRESS_WINDOW="$2";shift 2 ;;
    --help|-h)    sed -n '2,15p' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*)           echo "Unknown flag: $1" >&2; exit 1 ;;
    *)            SLUG="$1"; shift ;;
  esac
done

if [[ -z "$SLUG" ]]; then
  echo "Usage: pi-run <slug> [options]" >&2
  exit 1
fi

RUN_FILE="${RUNS_DIR}/${SLUG}.yaml"
PROGRESS_FILE="${RUNS_DIR}/${SLUG}.progress.md"
NOTES_FILE="${RUNS_DIR}/${SLUG}.notes"
STATE_FILE="${RUNS_DIR}/${SLUG}.state"

# ── Helpers ──────────────────────────────────────────────────────────

die() { echo "ERROR: $*" >&2; exit 1; }

ensure_run_exists() {
  [[ -f "$RUN_FILE" ]] || die "Run file not found: $RUN_FILE"
}

yq_field() {
  yq -r ".$1 // \"\"" "$RUN_FILE"
}

# State vars (loaded via source)
ROUND=0; BEST=""; BEST_ROUND=0; STATUS="active"

load_state() {
  if [[ -f "$STATE_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$STATE_FILE"
  fi
}

save_state() {
  printf 'ROUND=%s\nBEST=%s\nBEST_ROUND=%s\nSTATUS=%s\n' \
    "$ROUND" "$BEST" "$BEST_ROUND" "$STATUS" > "$STATE_FILE"
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
  mkdir -p "$RUNS_DIR"
  printf -- '- %s\n' "$NOTE_MSG" >> "$NOTES_FILE"
  echo "Note added."
  exit 0
fi

# --status
if [[ "$STATUS_ONLY" == true ]]; then
  ensure_run_exists
  load_state
  run_state="$(yq_field state)"
  echo "Run:    $SLUG"
  echo "State:  ${run_state:-pending}"
  echo "Round:  $ROUND"
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
load_state
init_progress

# Refuse to run archived runs
run_state="$(yq_field state)"
if [[ "$run_state" == "archived" ]]; then
  echo "Run '$SLUG' is archived. Set state: pending in $RUN_FILE to reactivate."
  exit 1
fi

# Refuse to re-run completed runs
if [[ "$run_state" == "done" ]]; then
  echo "Run '$SLUG' is already done. Set state: pending in $RUN_FILE to re-run."
  exit 0
fi

STATUS="active"
save_state

printf '\n%s\n  pi-run: %s\n%s\n\n' \
  "═══════════════════════════════════════════" \
  "$SLUG" \
  "═══════════════════════════════════════════"

while true; do
  ROUND=$((ROUND + 1))
  save_state

  printf '── Round %s ──────────────────────────\n' "$ROUND"

  prompt="$(build_prompt)"

  # Dry run
  if [[ "$DRY_RUN" == true ]]; then
    printf '%s\n' "$prompt"
    ROUND=$((ROUND - 1)); save_state
    exit 0
  fi

  round_log="${RUNS_DIR}/${SLUG}.round-$(printf '%03d' "$ROUND").log"
  echo "  Running session..."
  echo "  Log -> ${round_log}"

  # Resolve extra model/thinking args
  mapfile -t extra_args < <(resolve_model_args)

  # Run fresh pi session; capture output in log file
  pi --print \
    --no-session \
    --no-skills \
    --no-context-files \
    "${extra_args[@]}" \
    "$prompt" > "$round_log" 2>&1

  pi_exit=$?
  output=""
  [[ -f "$round_log" ]] && output="$(cat "$round_log")"

  # On hard failure with no output at all, skip round
  if [[ $pi_exit -ne 0 && -z "$output" ]]; then
    echo "  ! Session error (exit $pi_exit), skipping round"
    append_progress "$ROUND" "error" "session failed exit=$pi_exit"
    save_state
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
  save_state

  echo "  Verdict: $verdict"
  echo "  Summary: $summary"
  echo ""

  if [[ "$verdict" == "end" ]]; then
    STATUS="completed"; save_state
    yq -i '.state = "done"' "$RUN_FILE"
    printf '%s\n  Completed after %s rounds.\n%s\n\n' \
      "═══════════════════════════════════════════" \
      "$ROUND" \
      "═══════════════════════════════════════════"
    break
  fi

done
