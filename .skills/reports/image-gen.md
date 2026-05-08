# image-gen

- skill_id: `image-gen`
- status: `managed`
- skill_path: `image-gen`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

图片生成与编辑的首选方案。当需要生成图片、编辑已有图片、或批量生成并审批时触发。触发词："画一张""生成图片""image generation""edit this image""生成一批图让我 review""图片 gallery"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `image-gen/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
