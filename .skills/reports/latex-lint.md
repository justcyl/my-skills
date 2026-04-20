# latex-lint

- skill_id: `latex-lint`
- status: `managed`
- skill_path: `latex-lint`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

基于「打字抄能力」系列的 LaTeX 学术写作规范检查。当用户请求检查 LaTeX 源码规范、论文排版质量、proof 写作风格时触发。内置 linter 脚本自动检测常见问题（label 命名、引用格式、bracket sizing、BibTeX key、norm 写法、transpose、常数美学等），并提供修复建议。适用于："帮我检查 LaTeX""论文格式检查""lint my tex""proof 写法有没有问题""检查一下 overleaf 项目""notation 有没有问题"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `latex-lint/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
