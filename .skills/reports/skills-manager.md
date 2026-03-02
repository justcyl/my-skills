# skills-manager

- skill_id: `skills-manager`
- status: `managed`
- skill_path: `skills-manager`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

在当前 `my-skills` 仓库中统一发现、下载、创建、整理、审核、分发和发布 Skills 的总控 skill。Use when the user wants to: (1) 查找并下载 skill, (2) 创建新 skill, (3) 手动编辑 skill 后同步状态, (4) 管理向 Codex 或 Claude Code 的分发与发布。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `skills-manager/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
