# siliconflow-qwen-asr

- skill_id: `qwen-asr`
- status: `managed`
- skill_path: `qwen-asr`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

语音转文字技能（SiliconFlow优先，Qwen ASR兜底）。当需要处理语音消息、语音附件、音频文件或音频URL并提取可读文本时使用。支持本地音频与公网URL输入，默认先调用SiliconFlow /audio/transcriptions，失败后自动回退到Qwen3-ASR-Flash。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `qwen-asr/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
