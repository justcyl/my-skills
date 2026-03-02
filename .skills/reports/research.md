# research

- skill_id: `research`
- status: `managed`
- skill_path: `research`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

深度研究技术问题和代码库。使用 GitHub 代码搜索查找真实代码示例，使用 Exa 获取官方文档和最新网络内容。当需要查找代码模式、API 文档、最佳实践或解决技术问题时使用此技能。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `research/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
