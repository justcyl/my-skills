# image-gen

- skill_id: `image-gen`
- status: `managed`
- skill_path: `image-gen`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

多模型图片生成/编辑工具，通过本地代理统一调用 gemini-3.1-flash-image-preview、gpt-image-2、grok-4.2-image。
支持 text-to-image、image-to-image 编辑、1K/2K 分辨率切换、以及 Gallery HTML 可视化审批（--gallery）。
触发语境："画一张""生成图片""image generation""edit this image""生成一批图让我 review""图片 gallery"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `image-gen/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
