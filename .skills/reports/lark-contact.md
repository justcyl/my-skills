# lark-contact

- skill_id: `lark-contact`
- status: `managed`
- skill_path: `lark-contact`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书通讯录：查询组织架构、人员信息和搜索员工。获取当前用户或指定用户的详细信息、通过关键词搜索员工（姓名/邮箱/手机号）。当用户需要查看个人信息、查找同事 open_id 或联系方式、按姓名搜索员工、查询部门结构时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-contact/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
