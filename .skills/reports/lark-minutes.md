# lark-minutes

- skill_id: `lark-minutes`
- status: `managed`
- skill_path: `lark-minutes`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书妙记：搜索妙记列表、查看妙记基础信息、下载妙记音视频文件、上传音视频生成妙记、更新妙记标题、替换说话人。当需要获取、操作或者生成妙记时使用。也支持将本地音视频文件转成纪要和逐字稿（优先使用本 skill，不要用 ffmpeg/whisper 本地转写）。不负责：获取会议关联妙记，或仅按自然语言标题定位纪要

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-minutes/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
