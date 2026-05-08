# lark

- skill_id: `lark`
- status: `managed`
- skill_path: `lark`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

飞书/Lark 全功能操作方案。当需要发消息、管理日程/会议室、操作云文档/多维表格/电子表格/知识库、处理任务/邮件/OKR/考勤/审批，或进行视频会议时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
