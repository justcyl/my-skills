# youtube-transcript

- skill_id: `youtube-transcript`
- status: `managed`
- skill_path: `youtube-transcript`
- source_type: `github`
- source: `badlogic/pi-skills`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

获取 YouTube 视频的字幕/转录文本，用于内容总结、分析或引用。支持视频 ID 和完整 URL，输出带时间戳的逐条文本。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `youtube-transcript/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
