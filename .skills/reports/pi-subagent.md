# pi-subagent

- skill_id: `pi-subagent`
- status: `managed`
- skill_path: `pi-subagent`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

当需要启动子代理并行处理任务、或进行视觉审查时触发。触发词："spawn a sub-agent""调用子代理""pi --print""figure-qa""视觉审查"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pi-subagent/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
