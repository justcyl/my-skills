# rhetoric-of-decks

- skill_id: `rhetoric-of-decks`
- status: `managed`
- skill_path: `rhetoric-of-decks`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

基于 Rhetoric of Decks 哲学的幻灯片设计与生成指导。适用于"做个汇报""做 slides""做幻灯片""写个 deck""设计演示文稿""把论文做成 slides"等请求。涵盖 Beamer 与 RevealJS/Quarto 两种格式，提供从叙事结构、视觉设计到认知负荷优化的完整原则体系。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `rhetoric-of-decks/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
