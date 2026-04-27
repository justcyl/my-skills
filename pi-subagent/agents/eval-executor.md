---
name: eval-executor
description: Generic eval executor. Reads a skill and executes tasks following the skill's instructions, or executes tasks without a skill (baseline). Saves response to specified output path.
model: claude-sonnet
tools: read,bash
---

# eval-executor Agent

## 调用方式

```
bash ~/.agents/skills/pi-subagent/scripts/invoke.sh \
  --agent eval-executor \
  --msg '<structured task message>'
```

## 输入格式

Message 包含：
- 是否使用 skill（有 skill path 则读取并遵循，无则自然回答）
- 用户的原始消息
- 输出保存路径

## 输出格式

将完整响应文本写入指定的 `outputs/response.md`。

## 结果处理

主流程读取 `outputs/response.md` 评估输出质量。
