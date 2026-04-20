# tech-blog

- skill_id: `tech-blog`
- status: `managed`
- skill_path: `tech-blog`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

产出中文技术博客，重点解释工具/库/框架/技术路线背后的设计动机与哲学，而不只是功能说明。适用于“写一篇关于 X 的技术博客”“介绍 X 的设计思想”“解释 X 为什么这样设计”等请求。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `tech-blog/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
