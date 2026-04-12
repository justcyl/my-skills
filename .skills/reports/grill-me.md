# grill-me

- skill_id: `grill-me`
- status: `managed`
- skill_path: `grill-me`
- source_type: `github`
- source: `https://github.com/mattpocock/skills`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

与用户进行心智对齐——先展示对计划/设计的完整理解，再批量追问不确定之处，最终产出结构化对齐备忘录。适用于"grill me""帮我过一下这个方案""对齐一下想法""stress test my plan""review my design"等场景，尤其是在用户有了初步方案但需要被挑战和补全时。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `grill-me/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
