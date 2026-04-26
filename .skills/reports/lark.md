# lark

- skill_id: `lark`
- status: `managed`
- skill_path: `lark`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

飞书/Lark 全功能 CLI skill，合并 23 个子 skill。覆盖 IM（收发消息/群聊）、日历（日程/会议室）、云文档（Doc/Markdown/XML）、云空间（Drive/上传下载/权限）、多维表格（Base/字段/记录/视图）、电子表格（Sheets）、演示文稿（Slides）、任务（Task/清单）、邮件（Mail）、知识库（Wiki）、通讯录（Contact）、视频会议（VC/纪要）、事件订阅（Event/WebSocket）、OKR、画板（Whiteboard）、妙记（Minutes）、考勤（Attendance）、审批（Approval）及会议纪要/早报工作流。配合 lark-cli 命令行工具使用，需先完成 config init 和 auth login。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
