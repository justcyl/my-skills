# cli-creator

- skill_id: `cli-creator`
- status: `managed`
- skill_path: `cli-creator`
- source_type: `github`
- source: `https://github.com/archibate/dotfiles-opencode/tree/main/skills/cli-creator`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

从零到可用的 Agent-Native CLI：设计 agent-first 接口规范，从 API 文档/OpenAPI/curl 示例/SDK 构建可安装二进制，最后生成 companion skill。覆盖纯规范设计和完整实现两种场景。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `cli-creator/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
