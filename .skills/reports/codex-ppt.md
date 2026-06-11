# codex-ppt

- skill_id: `codex-ppt`
- status: `managed`
- skill_path: `codex-ppt`
- source_type: `github`
- source: `https://github.com/ningzimu/codex-ppt-skill`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

从文章、报告、论文、笔记或大纲生成视觉统一的全页图片式 PPT/PPTX 演示文稿；适合需要强视觉风格、统一版式和可直接汇报的 slides。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `codex-ppt/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
