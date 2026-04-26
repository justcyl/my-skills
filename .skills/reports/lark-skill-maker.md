# lark-skill-maker

- skill_id: `lark-skill-maker`
- status: `imported`
- skill_path: `lark-skill-maker`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

创建 lark-cli 的自定义 Skill。当用户需要把飞书 API 操作封装成可复用的 Skill（包装原子 API 或编排多步流程）时使用。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-skill-maker/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
