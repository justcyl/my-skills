---
name: paragraph-summarizer
description: 读取学术论文中文翻译，对语义载荷 ≥2 分的段落（含因果解释/设计决策/量化发现/对比分析）生成一句话摘要，输出 JSON 供主 agent 批量写入飞书评论
model: axonhub/gpt-5.4
thinking: off
tools: read,bash
---

# paragraph-summarizer

## 用途

批量处理中文翻译文件（`/tmp/<arxiv_id>_zh.md`），对**语义载荷 ≥2 分**的段落（含因果解释/设计决策/量化发现/对比分析）生成 `【段落摘要】`，写入 JSON 文件供主 agent 读取后批量添加飞书评论。纯过渡/引出/定义段落跳过不处理。

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
    "comment": "【段落摘要】含具体锚点的一句话",
    "score": 2
  }
]
```

`score` 字段：2=因果/设计/量化/对比段落，3=核心发现/消融关键节点。

## 主 agent 读取方式

```python
import json
with open('/tmp/<arxiv_id>_summaries.json') as f:
    summaries = json.load(f)
# 对每条调用 lark-cli drive +add-comment
```

## 失败处理

如果 OUTPUT 文件不存在或为空数组，主 agent 回退到手动逐段添加。
