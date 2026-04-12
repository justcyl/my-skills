---
name: youtube-transcript
description: 获取 YouTube 视频的字幕/转录文本，用于内容总结、分析或引用。支持视频 ID 和完整 URL，输出带时间戳的逐条文本。
---

# YouTube Transcript

获取 YouTube 视频的字幕转录文本，适用于内容摘要、分析、翻译或作为上下文输入。

## 触发条件

当用户提出以下请求时使用本 skill：
- "帮我总结这个 YouTube 视频"
- "获取这个视频的字幕"
- "转录这个 YouTube 链接"
- "分析这个视频的内容"

## 初始化

首次使用前需安装依赖（仅需一次）：

```bash
cd {baseDir}
npm install
```

## 用法

```bash
{baseDir}/transcript.js <video-id-or-url>
```

支持以下输入格式：
- 视频 ID：`EBw7gsDPAYQ`
- 完整 URL：`https://www.youtube.com/watch?v=EBw7gsDPAYQ`
- 短链接：`https://youtu.be/EBw7gsDPAYQ`

## 输出格式

带时间戳的逐条字幕文本：

```
[0:00] All right. So, I got this UniFi Theta
[0:15] I took the camera out, painted it
[1:23] And here's the final result
```

## 注意事项

- 视频必须已有字幕（手动上传或自动生成均可）
- 不支持无字幕视频
- 依赖 npm 包 `youtube-transcript-plus`
