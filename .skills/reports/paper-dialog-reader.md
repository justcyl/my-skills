# paper-dialog-reader

- skill_id: `paper-dialog-reader`
- status: `managed`
- skill_path: `paper-dialog-reader`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

通过 A/B 双 agent 对话式渐进披露深度解读 arXiv 论文。A 持有全文、给出结构化摘要，B 模拟未读原文的好奇读者、循环追问；用对话桥接作者意图与读者理解的 gap。适用于 '帮我深度读这篇论文'、'对话式阅读 arxiv:xxxx'、'dialog paper reading'、'渐进式论文解读' 等场景。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `paper-dialog-reader/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
