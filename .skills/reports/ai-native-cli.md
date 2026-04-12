# ai-native-cli

- skill_id: `ai-native-cli`
- status: `managed`
- skill_path: `ai-native-cli`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

从零到可用的 Agent-Native CLI：设计 agent-first 接口规范，从 API 文档/OpenAPI/curl 示例/SDK 构建可安装二进制，最后生成 companion skill。覆盖纯规范设计和完整实现两种场景。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `ai-native-cli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
