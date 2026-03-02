# session-logs

- skill_id: `session-logs`
- status: `managed`
- skill_path: `session-logs`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Search and analyze your own session logs (older/parent conversations) using jq.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `session-logs/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
