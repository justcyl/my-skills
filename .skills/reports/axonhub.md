# axonhub

- skill_id: `axonhub`
- status: `managed`
- skill_path: `axonhub`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

查询 AxonHub AI Gateway 的请求记录、Trace、UsageLog，以及管理渠道、API Key、模型等资源。使用官方 @axonhub/graphql-cli 工具通过 GraphQL API 操作，支持按 traceID、model、时间、状态筛选请求，也可探索 schema、执行任意 mutation。当用户需要查看 AxonHub 请求详情、排查 LLM 调用、查看 token 消耗、追踪 Trace、或通过命令行管理渠道/Key 时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `axonhub/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
