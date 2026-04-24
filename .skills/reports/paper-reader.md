# paper-reader

- skill_id: `paper-reader`
- status: `managed`
- skill_path: `paper-reader`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

辅助精读 AI/NLP 学术论文。逐节分析引言挖坑结构、相关工作踩人写法、图表叙事逻辑、实验设计思路与结论收尾。当用户说「帮我读这篇论文」「分析一下这篇paper的引言」「这个相关工作怎么写的」「帮我看看实验部分」「这篇paper的contribution是什么」「怎么学这篇paper的写法」时触发。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `paper-reader/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
