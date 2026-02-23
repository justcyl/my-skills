# API 参考（精简）

## SiliconFlow

- Endpoint: `POST https://api.siliconflow.cn/v1/audio/transcriptions`
- 认证: `Authorization: Bearer $SILICONFLOW_API_KEY`
- 请求: `multipart/form-data`
  - `file` (binary, 必填)
  - `model` (string, 必填)
- 响应: JSON，核心字段 `text`
- 限制（文档声明）:
  - 时长不超过 1 小时
  - 文件不超过 50MB

文档: https://docs.siliconflow.cn/cn/api-reference/audio/create-audio-transcriptions

## Qwen ASR（OpenAI兼容）

- Endpoint (CN): `POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- Endpoint (INTL): `POST https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions`
- 认证: `Authorization: Bearer $DASHSCOPE_API_KEY`
- 模型: `qwen3-asr-flash`
- 输入:
  - 公网 URL，或
  - Data URL（base64）
- 请求结构核心:
  - `messages[0].content[0].type = input_audio`
  - `messages[0].content[0].input_audio.data = <url|data-uri>`
  - `extra_body.asr_options.language`（可选）
  - `extra_body.asr_options.enable_itn`（可选）

文档: https://help.aliyun.com/zh/model-studio/qwen-asr-api-reference#f135c8a0befug
