# pi-subagent

- skill_id: `pi-subagent`
- status: `managed`
- skill_path: `pi-subagent`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

在 herdr pane 中用 pi --print 调度 sub-agent 的基础设施。
提供 agent 定义规范（frontmatter + system prompt）和通用调用模板。
调用前请先读懂 pi 参数含义，根据具体场景构造合适的命令，而非直接套用脚本。
触发语境："spawn a sub-agent""调用子代理""pi --print""figure-qa""视觉审查"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pi-subagent/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
