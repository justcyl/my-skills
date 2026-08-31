# hjfy-pdf-to-lark

- skill_id: `hjfy-pdf-to-lark`
- status: `managed`
- skill_path: `hjfy-pdf-to-lark`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

从 hjfy.top 论文页或 arXiv ID 获取中文翻译 PDF，并上传到用户自己的飞书云空间或知识库节点。用于“把幻觉翻译 PDF 导入飞书”“上传 hjfy 译文到飞书”“保存 arXiv 中文 PDF 到 Lark/Feishu”等请求；只研究方法时保持只读，明确要求导入时执行下载与上传。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `hjfy-pdf-to-lark/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
