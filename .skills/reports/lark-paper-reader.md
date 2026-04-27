# lark-paper-reader

- skill_id: `lark-paper-reader`
- status: `managed`
- skill_path: `lark-paper-reader`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

将学术论文（arXiv/DOI）全自动处理为飞书注释文档：ph+MinerU获取带图全文 → 中文翻译 → 创建飞书文档（统一文件夹）→ 插入原始图片 → 添加公式推导callout/段落摘要comment/术语注释 → 展开关键参考文献 → 自动质量检查（去重复图片/评论）。触发语境：'帮我读/翻译这篇论文'、'上传到飞书'、'arxiv://xxx 注释'、'给这篇paper做笔记'。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-paper-reader/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
