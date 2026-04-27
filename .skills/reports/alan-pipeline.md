# alan-pipeline

- skill_id: `alan-pipeline`
- status: `managed`
- skill_path: `alan-pipeline`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

管理研究项目的 card（知识单元）和 run（执行单元）。当用户需要记录实验发现、提出假设、做出决策、创建/执行研究任务时使用。Run 支持实验快照，确保 AI 训练实验可复现。适用于 alan/ 目录存在的项目。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `alan-pipeline/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
