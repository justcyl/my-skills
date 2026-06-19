# lark-shared

- skill_id: `lark-shared`
- status: `managed`
- skill_path: `lark-shared`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书/Lark CLI 共享规则：首次配置 lark-cli、登录授权、切换 user/bot 身份、处理权限不足或 _notice 更新提示时使用。CLI 更新可走 lark-cli update；Lark Skills 更新必须走 skills-manager 纳管、同步和分发。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-shared/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
