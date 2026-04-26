# lark-okr

- skill_id: `lark-okr`
- status: `imported`
- skill_path: `lark-okr`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书 OKR：管理目标与关键结果。查看和编辑 OKR 周期、目标（Objective）、关键结果（Key Result）、对齐关系、量化指标。当用户需要查看或创建 OKR、管理目标和关键结果、查看对齐关系时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-okr/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
