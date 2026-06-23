# lark-paper-reader-codex

- skill_id: `lark-paper-reader-codex`
- status: `managed`
- skill_path: `lark-paper-reader-codex`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Codex 专用：将 arXiv/DOI/PDF 学术论文整理为论文翻译飞书文档，正文以原文逐段中文翻译为主体。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-paper-reader-codex/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
