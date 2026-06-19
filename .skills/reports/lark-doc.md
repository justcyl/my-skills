# lark-doc

- skill_id: `lark-doc`
- status: `managed`
- skill_path: `lark-doc`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书云文档（Docx / Wiki 文档，v2 API）：读取和编辑飞书文档内容。当用户给出文档 URL 或 token，或需要查看、创建、编辑文档、插入或下载文档图片附件时使用。文档中嵌入的电子表格、多维表格、画板，先用本 skill 提取 token 再切到对应 skill。当用户给出 doubao.com 的 /docx/ 或 /wiki/ URL/token 时，也应直接使用本 skill；路由依据是 URL 路径模式和 token，而不是域名。不负责文档评论管理，也不负责表格或 Base 的数据操作。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-doc/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
