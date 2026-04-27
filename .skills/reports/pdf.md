# pdf

- skill_id: `pdf`
- status: `managed`
- skill_path: `pdf`
- source_type: `github`
- source: `anthropics/skills`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pdf/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
