# interactive-html

- skill_id: `interactive-html`
- status: `managed`
- skill_path: `interactive-html`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

生成带数据嵌入、JS 交互的单文件离线 HTML 页面。当用户要求生成交互式网页、可视化数据浏览器、单文件 SPA、带侧边栏导航的展示页、Markdown 渲染器时触发。触发词："做一个网页"、"生成 HTML"、"交互式展示"、"可视化"、"数据浏览器"。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `interactive-html/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
