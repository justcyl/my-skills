# academic-paper

- skill_id: `academic-paper`
- status: `managed`
- skill_path: `academic-paper`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

AI 学术论文全周期写作。覆盖选模板、文献调研、结构化写作、配图生成、格式检查、投稿前审查。
内置论文配图（figure-gen）与格式检查（format-check）子模块。
搭配 overleaf、gemini-image-gen、visual-checker 使用。
触发语境："写论文""paper writing""投稿前检查""画个架构图""论文配图""格式检查""desk reject"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `academic-paper/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
