# Paper Figure Generator

- skill_id: `paper-figure-gen`
- status: `created`
- skill_path: `paper-figure-gen`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `pending`

## Summary

Generate publication-quality figures for academic papers (architecture diagrams, pipeline overviews, concept illustrations). Uses gemini-image-gen as engine with academic prompt engineering, mandatory inspect-revise loop, and LaTeX snippet output.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `paper-figure-gen/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
