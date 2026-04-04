# run-in-tmux

- skill_id: `run-in-tmux`
- status: `managed`
- skill_path: `run-in-tmux`
- source_type: `github`
- source: `https://github.com/normful/picadillo`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

Use when the user wants to run commands in a new tmux session with split panes. Triggers on requests like "run X in tmux", "start a dev environment in tmux", or "open multiple terminals in tmux".

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `run-in-tmux/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
