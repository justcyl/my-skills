# officecli

- skill_id: `officecli`
- status: `managed`
- skill_path: `officecli`
- source_type: `github`
- source: `iOfficeAI/OfficeCLI`
- upstream_enabled: `true`
- risk_status: `blocked`

## Summary

Create, analyze, proofread, and modify Office documents (.docx, .xlsx, .pptx) using the officecli CLI tool. Use when the user wants to create, inspect, check formatting, find issues, add charts, or modify Office documents.

## Risk Findings

- mentions secrets, tokens, or private keys
- downloads and executes remote content

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `officecli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
