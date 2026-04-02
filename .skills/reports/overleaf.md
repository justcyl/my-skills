# overleaf

- skill_id: `overleaf`
- status: `managed`
- skill_path: `overleaf`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

通过 Git 和 Review API 与 Overleaf 项目交互。当用户需要克隆、编辑并推送 Overleaf 项目，或查看、定位、解决 review 评论线程，或触发编译、下载 PDF 时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `overleaf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
