# paper-format-check

- skill_id: `paper-format-check`
- status: `managed`
- skill_path: `paper-format-check`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

AI/NLP 顶会论文格式自动检查。适用于"检查论文格式""投稿前检查""camera-ready 检查""帮我看看格式对不对"等请求。覆盖 NeurIPS、ICML、ICLR、ACL/ARR、EMNLP、AAAI 等会议的页数、匿名性、引用、字体嵌入、图表质量等格式要求，含 PDF 转图视觉审查。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `paper-format-check/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
