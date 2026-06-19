# lark-paper-to-ppt

- skill_id: `lark-paper-to-ppt`
- status: `managed`
- skill_path: `lark-paper-to-ppt`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

将学术论文、论文 PDF、arXiv/DOI、或 lark-paper-reader-codex 生成的飞书论文读书文档整理成一份有用的飞书 Slides/PPT。用于把一篇或几篇论文变成可讲述、可复习、可分享的演示文稿，重点是提炼主线、选择论文原图、讲清方法、实验结果、insight 和局限；触发语境包括：把论文做成 PPT、做一份 paper slides、把这些 reader 文档整理成演示文稿、做文献汇报 slides、把同主题论文用 PPT 呈现。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-paper-to-ppt/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
