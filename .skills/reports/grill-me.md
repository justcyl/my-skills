# grill-me

- skill_id: `grill-me`
- status: `managed`
- skill_path: `grill-me`
- source_type: `github`
- source: `https://github.com/mattpocock/skills`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

当用户有了初步方案需要被挑战、补全或对齐时使用。适用于"grill me""帮我过一下这个方案""对齐一下想法""stress test my plan""review my design"等场景。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `grill-me/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
