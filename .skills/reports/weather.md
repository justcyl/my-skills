# weather

- skill_id: `weather`
- status: `managed`
- skill_path: `weather`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

Get current weather and forecasts (no API key required).

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `weather/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
