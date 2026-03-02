# gemini

- skill_id: `gemini`
- status: `managed`
- skill_path: `gemini`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

Gemini CLI for one-shot Q&A, summaries, and generation.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `gemini/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
