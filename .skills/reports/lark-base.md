# lark-base

- skill_id: `lark-base`
- status: `managed`
- skill_path: `lark-base`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

当需要用 lark-cli 操作飞书多维表格（Base）时调用：适用于建表、字段管理、记录读写、记录分享链接、视图配置、历史查询，以及角色/表单/仪表盘管理/工作流；也适用于把旧的 +table / +field / +record 写法改成当前命令写法。涉及字段设计、公式字段、查找引用、跨表计算、行级派生指标、数据分析需求时也必须使用本 skill。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-base/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
