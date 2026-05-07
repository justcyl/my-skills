# overleaf

- skill_id: `overleaf`
- status: `managed`
- skill_path: `overleaf`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

LaTeX 文档与 Overleaf 项目的首选方案。当需要编写或编辑 .tex 文件、编译 LaTeX 项目并获取 PDF、创建或管理 Overleaf 项目、查看或解决 review 评论时触发。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `overleaf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
