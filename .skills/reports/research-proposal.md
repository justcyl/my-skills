# research-proposal

- skill_id: `research-proposal`
- status: `managed`
- skill_path: `research-proposal`
- source_type: `local`
- source: `/tmp/research-proposal-skill.Fn5Cxr`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

将用户的 ML/AI 想法写成结构化研究提案。适用于“proposal / research plan / experiment plan / paper idea / write up my idea”等请求，尤其是在用户提供了假设或方法草图、希望补全相关工作、实验设计与成功判据时。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `research-proposal/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
