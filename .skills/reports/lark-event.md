# lark-event

- skill_id: `lark-event`
- status: `managed`
- skill_path: `lark-event`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书事件订阅：通过 WebSocket 长连接实时监听飞书事件（消息、通讯录变更、日历变更等），输出 NDJSON 到 stdout，支持 compact Agent 友好格式、正则路由、文件输出。当用户需要实时监听飞书事件、构建事件驱动管道时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-event/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
