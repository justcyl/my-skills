# lark-approval

- skill_id: `lark-approval`
- status: `managed`
- skill_path: `lark-approval`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

飞书审批：当前用户审批的查询与全部处理操作，覆盖待本人审批的任务与本人发起的实例。审批待办不是飞书任务（任务类待办走 lark-task）；不负责创建审批定义和发起新审批。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-approval/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
