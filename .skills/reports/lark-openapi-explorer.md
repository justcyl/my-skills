# lark-openapi-explorer

- skill_id: `lark-openapi-explorer`
- status: `managed`
- skill_path: `lark-openapi-explorer`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

飞书/Lark 原生 OpenAPI 探索：从官方文档库中挖掘未经 CLI 封装的原生 OpenAPI 接口。当用户的需求无法被现有 lark-* skill 或 lark-cli 已注册命令满足，需要查找并调用原生飞书 OpenAPI 时使用。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-openapi-explorer/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
