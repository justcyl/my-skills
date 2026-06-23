# lark-paper-reader-codex

- skill_id: `lark-paper-reader-codex`
- status: `managed`
- skill_path: `lark-paper-reader-codex`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Codex 专用：将学术论文整理为以原文逐段中文翻译为主体、再叠加精读注释的飞书文档。触发语境：arXiv/DOI/PDF 论文到飞书、帮我读这篇论文、给 paper 做 Codex 版飞书笔记。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-paper-reader-codex/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
