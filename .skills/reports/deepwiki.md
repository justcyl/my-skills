# deepwiki

- skill_id: `deepwiki`
- status: `managed`
- skill_path: `deepwiki`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

Query DeepWiki for repository documentation and structure. Use to understand open source projects, find API docs, and explore codebases.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `deepwiki/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
