# guizang-ppt-skill

- skill_id: `guizang-ppt-skill`
- status: `managed`
- skill_path: `guizang-ppt-skill`
- source_type: `github`
- source: `https://github.com/op7418/guizang-ppt-skill`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

生成"电子杂志 × 电子墨水"风格的横向翻页网页 PPT（单 HTML 文件），含 WebGL 流体背景、衬线标题 + 非衬线正文、章节幕封、数据大字报、图片网格等模板。当用户需要制作分享 / 演讲 / 发布会风格的网页 PPT，或提到"杂志风 PPT"、"horizontal swipe deck"、"editorial magazine"、"e-ink presentation"时使用。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `guizang-ppt-skill/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
