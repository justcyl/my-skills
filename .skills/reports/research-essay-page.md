# research-essay-page

- skill_id: `research-essay-page`
- status: `managed`
- skill_path: `research-essay-page`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

生成 metauto.ai/neuralcomputer 风格的学术研究随笔 HTML 页面。多文件架构（CSS/JS 静态不动，agent 只生成内容 HTML）。支持封面图、多章节、对比表格、代码卡片（syntax highlight）、KaTeX 公式（颜色标注）、多类型边注（术语/符号/译注）、内联引用、BibTeX 引用块、可折叠摘要、story-aside callout、图片 lightbox。适用于：把论文/博客/技术随笔生成为精美 HTML 发布页面。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `research-essay-page/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
