# html-slides

- skill_id: `html-slides`
- status: `managed`
- skill_path: `html-slides`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

单文件 HTML 幻灯片（Han Xiao 式固定舞台 deck）的制作方案。当需要做网页版 slides、HTML 幻灯片、会议演讲 deck、或希望用浏览器直接放映且导出 PDF 的演示文稿时使用。触发词："HTML slides""网页幻灯片""单文件 deck""hanxiao 风格 slides""做个网页版演讲稿"。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `html-slides/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
