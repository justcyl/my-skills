# pi-threads

- skill_id: `pi-threads`
- status: `managed`
- skill_path: `pi-threads`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

搜索、定位和阅读历史 pi 会话记录。当需要查找之前做得好的对话、提取 pattern 转化为 skill、或回顾过去的决策时使用。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pi-threads/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
