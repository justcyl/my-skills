---
name: paragraph-summarizer
description: 读取学术论文中文翻译，为每个实质性长段落生成一句话摘要，输出 JSON 供主 agent 批量写入飞书评论
model: axonhub/gpt-5.4
thinking: off
tools: read,bash
---

# paragraph-summarizer

## 用途

批量处理中文翻译文件（`/tmp/<arxiv_id>_zh.md`），为每个长段落生成 `【段落摘要】`，写入 JSON 文件供主 agent 读取后批量添加飞书评论。

## 调用方式

在 herdr pane 中运行（主 agent 不等待，继续 Step 3/4）：

```bash
SKILL_DIR=~/.agents/skills/lark-paper-reader

pi --print \
  --model axonhub/gpt-5.4 \
  --thinking off \
  --tools read,bash \
  --system-prompt "$SKILL_DIR/agents/paragraph-summarizer.prompt.md" \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  "ZH_MD=/tmp/<arxiv_id>_zh.md OUTPUT=/tmp/<arxiv_id>_summaries.json"
```

## 输入格式

消息中包含两个 key-value：
- `ZH_MD=<path>`：中文翻译文件路径
- `OUTPUT=<path>`：结果 JSON 输出路径

## 输出格式

写入 OUTPUT 路径的 JSON 数组：

```json
[
  {
    "para_start": "段落开头前 30 个字（唯一定位用）",
    "comment": "【段落摘要】一句话说明这段在讲什么"
  }
]
```

## 主 agent 读取方式

```python
import json
with open('/tmp/<arxiv_id>_summaries.json') as f:
    summaries = json.load(f)
# 对每条调用 lark-cli drive +add-comment
```

## 失败处理

如果 OUTPUT 文件不存在或为空数组，主 agent 回退到手动逐段添加。
