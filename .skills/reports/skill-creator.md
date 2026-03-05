# skill-creator

- skill_id: `skill-creator`
- status: `managed`
- skill_path: `skill-creator`
- source_type: `github`
- source: `https://github.com/anthropics/skills/tree/main/skills/skill-creator`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `skill-creator/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
