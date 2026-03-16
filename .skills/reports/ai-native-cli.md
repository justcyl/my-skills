# ai-native-cli

- skill_id: `ai-native-cli`
- status: `managed`
- skill_path: `ai-native-cli`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

设计 AI-Native CLI 接口规范——agent-first, human-compatible。命令树、参数、响应信封、错误码、分页、文档分层，全部为 agent 消费优化。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `ai-native-cli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
