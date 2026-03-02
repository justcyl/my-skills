# siliconflow-qwen-asr

- skill_id: `qwen-asr`
- status: bootstrapped
- source_type: `local-bootstrap`
- upstream_enabled: `false`
- managed_path: `catalog/skills/qwen-asr/managed`

## Summary

语音转文字技能（SiliconFlow优先，Qwen ASR兜底）。当需要处理语音消息、语音附件、音频文件或音频URL并提取可读文本时使用。支持本地音频与公网URL输入，默认先调用SiliconFlow /audio/transcriptions，失败后自动回退到Qwen3-ASR-Flash。

## Notes

- This skill was registered from the current repository as part of the initial bootstrap.
- No upstream source is configured yet.
- Future updates require either manual edits in `managed/` or explicit source registration.
