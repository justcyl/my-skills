# skills-manager

- skill_id: `skills-manager`
- status: `managed`
- skill_path: `skills-manager`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

统一处理所有 skills 操作的总控 skill，包括搜索、导入、创建、重构、编辑、优化、上游跟踪、分发、归档与发布。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `skills-manager/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
