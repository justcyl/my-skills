# lark-mail

- skill_id: `lark-mail`
- status: `managed`
- skill_path: `lark-mail`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书邮箱：起草、撰写、发送、回复、转发、读取和搜索邮件；管理草稿、文件夹、标签、联系人、附件和收信规则。当用户提到起草邮件、写邮件、发通知邮件、回复/转发/查看/搜索邮件、收件箱、邮件会话、编辑草稿、下载附件、邮件文件夹/标签/联系人、监听新邮件、收信规则，或 draft、compose、send email、reply、forward、inbox、mail thread、mail rules 时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-mail/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
