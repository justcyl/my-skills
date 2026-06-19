# lark-contact

- skill_id: `lark-contact`
- status: `managed`
- skill_path: `lark-contact`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

飞书 / Lark 通讯录:按姓名 / 邮箱解析成 open_id,或按 open_id 反查姓名 / 部门 / 邮箱 / 联系方式 / 个人状态 / 签名。当用户提到某人姓名要下一步发消息 / 排日程,或拿到 open_id 想查具体信息时使用。不负责部门树遍历、按部门列员工、组织架构图,这类需求走原生 OpenAPI。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-contact/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
