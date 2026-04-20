# gemini-image-gen

- skill_id: `gemini-image-gen`
- status: `managed`
- skill_path: `gemini-image-gen`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Generate/edit images with Gemini image models (default: gemini-3.1-flash-image-preview).
Use for any image create/modify request. Supports text-to-image + image-to-image editing;
1K/2K/4K resolution; base-url gateways and provider fallback (gemini-native/openai-chat-compat).
Use --model to select a different model.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `gemini-image-gen/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
