# academic-paper

- skill_id: `academic-paper`
- status: `managed`
- skill_path: `academic-paper`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

学术论文写作的完整方案。当需要写论文、生成论文配图、检查投稿格式或进行投稿前审查时触发。触发词："写论文""paper writing""投稿前检查""画个架构图""论文配图""格式检查""desk reject"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `academic-paper/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
