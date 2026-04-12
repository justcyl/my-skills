# btca-local

- skill_id: `btca-local`
- status: `managed`
- skill_path: `btca-local`
- source_type: `github`
- source: `https://github.com/davis7dotsh/better-context`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

本地 Git 仓库搜索助手。当用户说"use btca"、要求搜索/查阅某个 GitHub 仓库的代码或文档、或需要基于本地已克隆仓库回答技术问题时触发。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `btca-local/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
