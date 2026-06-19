# lark-event

- skill_id: `lark-event`
- status: `managed`
- skill_path: `lark-event`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书/Lark 实时事件监听、订阅和消费：通过 `lark-cli event consume <EventKey>` 输出 NDJSON 事件流，覆盖 IM 消息/表情/群变更、视频会议结束、妙记生成、画板更新等。适用于机器人实时消息处理、长时间订阅、webhook/push handler；支持 `--max-events`、`--timeout` 有界运行和 stderr ready-marker，方便 AI Agent 作为子进程编排。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-event/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
