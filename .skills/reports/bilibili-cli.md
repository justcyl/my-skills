# bilibili-cli

- skill_id: `bilibili-cli`
- status: `managed`
- skill_path: `bilibili-cli`
- source_type: `github`
- source: `https://github.com/public-clis/bilibili-cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

CLI skill for Bilibili (哔哩哔哩, B站) with token-efficient YAML output for AI agents to browse videos, users, search, trending, dynamics, favorites, and interactions from the terminal

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `bilibili-cli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
