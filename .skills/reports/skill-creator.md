# skill-creator

- skill_id: `skill-creator`
- status: `managed`
- skill_path: `skill-creator`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `skill-creator/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
