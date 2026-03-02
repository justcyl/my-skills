# summarize

- skill_id: `summarize`
- status: `managed`
- skill_path: `summarize`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Summarize or extract text/transcripts from URLs, podcasts, and local files (great fallback for “transcribe this YouTube/video”).

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `summarize/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
