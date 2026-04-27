---
name: figure-qa
description: AI 生成图片视觉 QA。支持 academic / slides / general 三种场景，输出结构化 Figure QA Report，含 PASS/MINOR/REGENERATE 判定和重生成指引。
model: axonhub/gemini-3.1-pro-preview
thinking: off
tools: read,bash
---

# figure-qa Agent

AI 生成图片的视觉质量 QA。先压缩图片再用视觉模型审查，输出结构化报告。

> System prompt 在同目录 `figure-qa.prompt.md`。

---

## 调用方式

调用前请确认参数均正确，再构造最终命令。

**参考命令：**

```bash
pi --print \
  --model axonhub/gemini-3.1-pro-preview \
  --thinking off \
  --tools read,bash \
  --system-prompt ~/.agents/skills/pi-subagent/agents/figure-qa.prompt.md \
  --no-skills \
  --no-context-files \
  --no-extensions \
  --no-session \
  'Check the image at: <absolute-path>
Scene: <academic|slides|general>
Intent: <what the image should show>
[optional extra context]'
```

> system-prompt 路径根据你的实际部署位置调整。

### herdr 四步模式

**Step 1 — Split pane**

```json
{ "action": "pane_split", "direction": "down", "newPane": "figure-qa" }
```

**Step 2 — Run**（将上方参考命令填入 command，替换 `<path>`/`<scene>`/`<intent>`）

```json
{
  "action": "run",
  "pane": "figure-qa",
  "command": "<根据上方模板构造的完整 pi --print 命令>"
}
```

**Step 3 — Wait**

```json
{
  "action": "wait_agent",
  "pane": "figure-qa",
  "statuses": ["done", "idle"],
  "timeout": 120000
}
```

**Step 4 — Read**

```json
{
  "action": "read",
  "pane": "figure-qa",
  "source": "recent-unwrapped",
  "lines": 100
}
```

定位输出中的 `## Figure QA Report` 段。

### Batch QA（多张图复用同一 pane）

```
run → wait_agent → read → run → wait_agent → read → ...
```

不需要重新 split pane。

---

## 输入格式（`--msg` 内容）

```text
Check the image at: <absolute-path>
Scene: academic | slides | general
Intent: <what the image should show>
[optional extra context]
```

**Scene 选择：**

| scene | 适用场景 |
|-------|---------|
| `academic` | 论文配图：flat vector 风格、白底、标注可读、出版级美观 |
| `slides` | 演示幻灯片：字号、对比度、布局、不溢出 |
| `general` | 通用图片：内容保真、视觉质量、artifact、文字渲染 |

---

## 输出格式

```markdown
## Figure QA Report

**File**: <image_path>
**Scene**: <academic | slides | general>
**Verdict**: ✅ PASS / ⚠️ MINOR ISSUES / ❌ REGENERATE

### Summary
<一句话总结>

### Issues Found

| Severity | Issue | Location |
|----------|-------|----------|
| Critical | ...   | ...      |
| Minor    | ...   | ...      |

### What's Good
- ...

### Regeneration Guidance
<具体修复建议或 "No regeneration needed">
```

---

## 结果处理

| Verdict | 动作 |
|---------|------|
| ✅ PASS | 直接使用图片 |
| ⚠️ MINOR ISSUES | 酌情重新生成；minor 问题通常可接受 |
| ❌ REGENERATE | 将 Regeneration Guidance 反馈给生成调用并重试 |

---

## 完成后清理 pane

```json
{ "action": "stop", "pane": "figure-qa" }
```
