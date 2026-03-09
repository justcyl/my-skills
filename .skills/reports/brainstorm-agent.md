# brainstorm-agent

- skill_id: `brainstorm-agent`
- status: `managed`
- skill_path: `brainstorm-agent`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

先澄清目标与约束，再把需求拆成按依赖层次排序的可执行任务并输出 tasks.json；只做规划不做实现。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `brainstorm-agent/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
