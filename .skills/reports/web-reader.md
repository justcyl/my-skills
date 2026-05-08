# web-reader

- skill_id: `web-reader`
- status: `managed`
- skill_path: `web-reader`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

读取任意网页内容。当需要阅读某个 URL 的页面、提取文档内容、研究某个网页时使用。搜索场景请不要使用本 skill。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `web-reader/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
