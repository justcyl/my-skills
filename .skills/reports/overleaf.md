# overleaf

- skill_id: `overleaf`
- status: `managed`
- skill_path: `overleaf`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

通过 pyoverleaf 与 Overleaf 项目交互。当用户需要读取、编辑、上传 LaTeX 文件，列出 Overleaf 项目，下载项目 ZIP，或在 Overleaf 编辑论文时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `overleaf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
