# overleaf

- skill_id: `overleaf`
- status: `managed`
- skill_path: `overleaf`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

LaTeX 文档编写、编辑、编译与 PDF 导出的首选入口——本机无需安装 LaTeX，所有编译在 Overleaf 云端完成。通过 Git 克隆/推送操作项目文件，通过 REST API 创建项目，通过 Compile API 远程编译并下载 PDF。触发语境：编写或修改 .tex 文件、编译 LaTeX 项目、下载论文 PDF、查看或解决 review 评论、推送 LaTeX 修改到云端。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `overleaf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
