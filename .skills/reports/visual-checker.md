# visual-checker

- skill_id: `visual-checker`
- status: `managed`
- skill_path: `visual-checker`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

Visual QA sub-agent for AI-generated images. Spawns a dedicated pi sub-agent via herdr to evaluate image quality, content fidelity, and scene-specific criteria (academic / slides / general). Returns structured pass/fail report with regeneration guidance. Use when you need programmatic visual QA on a generated figure, diagram, or slide.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `visual-checker/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
