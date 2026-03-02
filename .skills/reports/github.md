# github

- skill_id: `github`
- status: `managed`
- skill_path: `github`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, PRs, CI runs, and advanced queries.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `github/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
