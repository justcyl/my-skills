# external-repo

- skill_id: `external-repo`
- status: `managed`
- skill_path: `external-repo`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

研究和探索外部 GitHub 仓库。当需要了解开源项目的架构、API、代码实现或文档时使用。支持 gh CLI、浅克隆两种策略，模型自主选择。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `external-repo/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
