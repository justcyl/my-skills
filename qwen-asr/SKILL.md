---
name: siliconflow-qwen-asr
description: 语音转文字技能（SiliconFlow优先，Qwen ASR兜底）。当需要处理语音消息、语音附件、音频文件或音频URL并提取可读文本时使用。支持本地音频与公网URL输入，默认先调用SiliconFlow /audio/transcriptions，失败后自动回退到Qwen3-ASR-Flash。
---

# SiliconFlow + Qwen ASR

使用 `scripts/transcribe.py` 做统一转写入口：
- 默认：SiliconFlow 优先，失败自动 fallback 到 Qwen
- 可强制指定 provider
- 输入支持本地文件或 URL

## 快速开始

```bash
# 1) 安装依赖
pip install requests

# 2) 配置密钥（建议都配）
export SILICONFLOW_API_KEY="sk-..."
export DASHSCOPE_API_KEY="sk-..."

# 3) 自动模式（推荐）
python scripts/transcribe.py /path/to/audio.mp3
python scripts/transcribe.py "https://example.com/audio.mp3"
```

## 常用命令

```bash
# 强制仅用 SiliconFlow
python scripts/transcribe.py audio.mp3 --provider siliconflow

# 强制仅用 Qwen
python scripts/transcribe.py audio.mp3 --provider qwen

# Qwen 国际站
python scripts/transcribe.py audio.mp3 --provider qwen --qwen-region intl

# Qwen 指定语种 + ITN
python scripts/transcribe.py audio.mp3 --provider qwen --language zh --enable-itn
```

## 在会话中处理语音消息的流程

1. 拿到语音文件路径或语音URL。
2. 执行：`python scripts/transcribe.py <audio>`。
3. 将输出文本直接用于总结、翻译、提炼行动项。
4. 若日志出现 `[WARN] SiliconFlow失败`，表示已自动回退到Qwen并继续处理。

## 关键参数

- `--provider auto|siliconflow|qwen`：选择调用策略（默认 `auto`）
- `--sf-model`：SiliconFlow模型（默认 `FunAudioLLM/SenseVoiceSmall`）
- `--qwen-model`：Qwen模型（默认 `qwen3-asr-flash`）
- `--qwen-region cn|intl`：Qwen地域
- `--language`：Qwen已知语种时可指定
- `--enable-itn`：Qwen数字/日期规范化（中英文更有用）

## 参考资料

- [references/api_reference.md](references/api_reference.md)
