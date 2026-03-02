# coding-agent

- skill_id: `coding-agent`
- status: `managed`
- skill_path: `coding-agent`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Run Codex CLI, Claude Code, OpenCode, or Pi Coding Agent via background process for programmatic control.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `coding-agent/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
