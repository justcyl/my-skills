# mole-release-notes

- skill_id: `mole-release-notes`
- status: `managed`
- skill_path: `mole-release-notes`
- source_type: `local`
- source: `/Users/chenyl/.btca/agent/sandbox/tw93-mole/.claude/skills/release-notes`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

为 tw93/Mole 的 V<version> 标签撰写和发布双语 GitHub Release notes。仅在用户明确要求 Mole 发布说明、release notes、发版文案或发布到 GitHub Release 时使用。默认只起草, 只有用户明确说 publish/发布/提交后才允许调用 gh release edit 和追加 reactions。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `mole-release-notes/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
