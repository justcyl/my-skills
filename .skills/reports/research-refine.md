# research-refine

- skill_id: `research-refine`
- status: `managed`
- skill_path: `research-refine`
- source_type: `github`
- source: `https://github.com/zjYao36/Auto-Research-Refine`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

Turn a vague research direction into a problem-anchored, elegant, frontier-aware, implementation-oriented method plan via iterative GPT-5.4 review. Use when the user says "refine my approach", "帮我细化方案", "decompose this problem", "打磨idea", "refine research plan", "细化研究方案", or wants a concrete research method that stays simple, focused, and top-venue ready instead of a vague or overbuilt idea.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `research-refine/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
