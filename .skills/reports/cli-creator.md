# cli-creator

- skill_id: `cli-creator`
- status: `managed`
- skill_path: `cli-creator`
- source_type: `github`
- source: `https://github.com/archibate/dotfiles-opencode/tree/main/skills/cli-creator`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

Spec CLI surface area before implementation - command tree, flags, exit codes, I/O contract. Use when designing or planning a CLI interface.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `cli-creator/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
