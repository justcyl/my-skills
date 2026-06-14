# lark-paper-reader-codex

- skill_id: `lark-paper-reader-codex`
- status: `managed`
- skill_path: `lark-paper-reader-codex`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Codex 专用：将学术论文整理为飞书注释文档。触发语境：帮我读/翻译这篇论文、上传到飞书、arxiv://xxx 注释、给 paper 做 Codex 版飞书笔记。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-paper-reader-codex/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
