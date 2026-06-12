# anti-fable

- skill_id: `anti-fable`
- status: `managed`
- skill_path: `anti-fable`
- source_type: `github`
- source: `https://github.com/HughYau/anti-fable`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

Transform dense technical, scientific, computing, network, safety, policy, or life-science research questions into clear source-domain-neutral fables for non-specialists. Use when the user asks to allegorize, fable-ize, turn complex research into a metaphorical story, explain without jargon, produce both plain and more imaginative fable versions, or reduce audience reliance on source-field associations while preserving the reasoning structure. Do not use to hide harmful intent, circumvent safety policies, or obtain instructions that would be disallowed if asked directly.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `anti-fable/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
