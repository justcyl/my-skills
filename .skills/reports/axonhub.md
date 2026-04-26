# axonhub

- skill_id: `axonhub`
- status: `managed`
- skill_path: `axonhub`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

查询 AxonHub AI Gateway 的请求记录、Trace、UsageLog。通过 GraphQL API 认证登录并检索请求体/响应体/延迟/token 用量，支持按 traceID、model、时间范围、状态筛选。当用户需要查看 AxonHub 某个请求详情、排查 LLM 调用、查看 token 消耗、或追踪特定 Trace 下的所有请求时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `axonhub/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
