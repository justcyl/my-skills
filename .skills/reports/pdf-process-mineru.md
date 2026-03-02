# pdf-process-mineru

- skill_id: `pdf-process-mineru`
- status: `managed`
- skill_path: `pdf-process-mineru`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

PDF document parsing tool based on local MinerU, supports converting PDF to Markdown, JSON, and other machine-readable formats.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pdf-process-mineru/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
