# lark-task

- skill_id: `lark-task`
- status: `managed`
- skill_path: `lark-task`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书任务：管理任务、清单和任务智能体。创建待办任务、查看和更新任务状态、拆分子任务、组织任务清单、分配协作成员、上传任务附件、注册或注销任务智能体、更新任务智能体的主页数据、写入智能体任务记录。当用户需要创建待办事项、查看任务列表、跟踪任务进度、管理项目清单或给他人分配任务、为任务上传附件文件、注册注销任务智能体、更新智能体主页数据、写入任务记录时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-task/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
