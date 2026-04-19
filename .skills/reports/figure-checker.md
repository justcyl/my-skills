# figure-checker

- skill_id: `figure-checker`
- status: `managed`
- skill_path: `figure-checker`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

Visual QA sub-agent for AI-generated images. Spawns a dedicated pi sub-agent via herdr to evaluate image quality, content fidelity, and scene-specific criteria (academic / slides / general). Returns structured pass/fail report with regeneration guidance. Use when you need programmatic visual QA on a generated figure, diagram, or slide.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `figure-checker/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
