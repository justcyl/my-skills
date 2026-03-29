# baoyu-youtube-transcript

- skill_id: `baoyu-youtube-transcript`
- status: `managed`
- skill_path: `baoyu-youtube-transcript`
- source_type: `github`
- source: `https://github.com/jimliu/baoyu-skills`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

Downloads YouTube video transcripts/subtitles and cover images by URL or video ID. Supports multiple languages, translation, chapters, and speaker identification. Caches raw data for fast re-formatting. Use when user asks to "get YouTube transcript", "download subtitles", "get captions", "YouTube字幕", "YouTube封面", "视频封面", "video thumbnail", "video cover image", or provides a YouTube URL and wants the transcript/subtitle text or cover image extracted.

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `baoyu-youtube-transcript/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
