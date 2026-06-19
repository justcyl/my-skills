# lark-task

- skill_id: `lark-task`
- status: `managed`
- skill_path: `lark-task`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书任务：管理任务和清单。创建待办任务、查看和更新任务状态、拆分子任务、组织任务清单、分配协作成员。当用户需要创建待办事项、查看任务列表、跟踪任务进度、管理项目清单或给他人分配任务时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-task/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
