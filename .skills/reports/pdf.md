# pdf

- skill_id: `pdf`
- status: `managed`
- skill_path: `pdf`
- source_type: `github`
- source: `anthropics/skills`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

当用户需要处理 PDF 文件时使用此 skill。包括：读取/提取 PDF 中的文本或表格、合并多个 PDF、拆分 PDF、旋转页面、添加水印、新建 PDF、填写 PDF 表单、加密/解密 PDF、提取图片、对扫描版 PDF 进行 OCR 识别。只要用户提到 .pdf 文件或需要生成 PDF，都应激活此 skill。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pdf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
