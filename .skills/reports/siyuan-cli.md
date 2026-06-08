# siyuan-cli

- skill_id: `siyuan-cli`
- status: `managed`
- skill_path: `siyuan-cli`
- source_type: `github`
- source: `https://github.com/cicbyte/siyuan-cli.git`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

操作思源笔记的 CLI 工具。当用户要求管理思源笔记的笔记本、文档、块、标签、搜索、SQL 查询、导入导出、资源、同步，或配置 auth、AI chat、MCP Server 时使用此 skill。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `siyuan-cli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
