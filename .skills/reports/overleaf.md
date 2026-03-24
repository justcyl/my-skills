# overleaf

- skill_id: `overleaf`
- status: `managed`
- skill_path: `overleaf`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

通过 pyoverleaf 与 Overleaf 项目交互。当用户需要读取、编辑、上传 LaTeX 文件，列出 Overleaf 项目，下载项目 ZIP，或在 Overleaf 编辑论文时使用。所有写操作（write、mkdir、rm）必须先向用户展示变更内容并等待确认，绝不自动推送。依赖环境变量 OVERLEAF_COOKIE 和 OVERLEAF_HOST。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `overleaf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
