# lark-paper-reader

- skill_id: `lark-paper-reader`
- status: `managed`
- skill_path: `lark-paper-reader`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

将学术论文整理为飞书注释文档。触发语境："帮我读/翻译这篇论文""上传到飞书""arxiv://xxx 注释""给这篇 paper 做笔记"。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-paper-reader/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
