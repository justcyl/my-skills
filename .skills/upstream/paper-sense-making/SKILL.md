# SKILL.md — skill-paper-sensemaking

## Skill 类型

**Prompt-based conversational skill**（非 tool-call 型）

核心执行体是 `prompt/system-prompt.md`，通过 system prompt 注入 AI 环境运行。Canvas 是只读展示界面，所有交互在 AI 对话中完成。

---

## 这个 Skill 做什么

大多数"AI 读论文"工具的流程是：

```
paper → summary
```

这个 skill 的流程是：

```
paper × 用户的认知假设 → 冲突 → 表态 → 重构 → 认知 delta 可视化
```

核心差异：**sensemaking ≠ 理解，= 认知重构**

---

## 使用方式

### Step 1：注入 system prompt

将 `prompt/system-prompt.md` 的内容注入到：
- Claude Project 的 system prompt
- OpenClaw skill 配置
- 任何支持 system prompt 的 AI 环境

不作为工具动态加载，不需要 function calling。

### Step 2：触发

```
/sensemaking
profile: 初中数学老师，正在设计几何 proof 的反馈工具

[粘贴论文全文]
```

### Step 3：完成三幕对话

AI 引导用户走过三幕：理解 → 冲突 → 重构。所有交互在对话窗口完成。

### Step 4：渲染 Canvas

对话结束后，AI 输出完整 JSON。
打开 `artifact/sensemaking-canvas.html`，粘贴 JSON，点"渲染认知轨迹"。

---

## 三幕结构

| 幕 | 名称 | 核心问题 | AI 行为 |
|----|------|----------|---------|
| 一 | 理解 Comprehension | paper 说了什么？对你意味着什么？ | 输出理解，probe 确认 |
| 二 | 冲突 Collision | 你原来的认知假设 vs paper 挑战 | 暴露摩擦，要求用户表态，追问 |
| 三 | 重构 Reconstruction | 认知改变了什么？你打算做什么？ | 总结 delta，收集 one change，输出 JSON |

---

## 组件清单

```
skill-paper-sensemaking/
│
├── SKILL.md                           ← 你在这里
│
├── prompt/
│   └── system-prompt.md               ← 注入 AI 环境的完整 system prompt
│
├── artifact/
│   └── sensemaking-canvas.html        ← 只读 canvas，粘贴 JSON 渲染认知轨迹
│
├── assets/
│   ├── pedagogy-reference.md          ← 教学法参考库（供 AI 内部参考）
│   └── paper-archetypes.md            ← 论文类型分类（供 AI 内部参考）
│
├── examples/
│   ├── example-input.md               ← 触发示例（多种 profile 场景）
│   └── example-output.json            ← 完整示例 JSON（真实对话结果）
│
├── docs/
│   ├── design-decisions.md            ← 设计决策记录
│   └── pipeline-interface.md          ← JSON schema + 上下游接口规范
│
└── README.md
```

---

## JSON 输出契约

```json
{
  "meta": {
    "paper_title": "string",
    "profile_read": "string",
    "session_date": "YYYY-MM-DD"
  },
  "act1_comprehension": {
    "core_claim": "string",
    "learning_mechanism": "string（箭头格式）",
    "user_perspective": "string"
  },
  "act2_collision": {
    "user_schema_before": "string",
    "paper_challenge": "string",
    "friction": "string",
    "user_stance": "agree | unsure | disagree",
    "user_reasoning": "string",
    "probe_exchange": [
      { "probe": "string", "response": "string" }
    ]
  },
  "act3_reconstruction": {
    "before": "string",
    "after": "string",
    "delta": "string",
    "one_change": "string"
  }
}
```

详见 `docs/pipeline-interface.md`。

---

## Pipeline 位置

```
skill-user-profile ──→ skill-paper-discovery
                                ↓
                   skill-paper-sensemaking   ← 你在这里
                                ↓
              ┌─────────────────┴──────────────────┐
              ↓                                    ↓
skill-visual-knowledge-design          skill-paper-to-prd
```

**前提条件：**
- 用户 profile 已知（一句话即可，不需要结构化）
- Paper 已选定（用户 paste 全文或摘要）

---

## L 等级

**L2** — 多步骤 workflow，人在循环中

AI 引导 → 用户回应 → AI 追问 → 用户深入 → AI 总结输出

---

## 后续指令（JSON 输出后）

| 指令 | 作用 |
|------|------|
| `/深挖 [某个冲突点]` | 苏格拉底式继续追问 |
| `/prd` | 把 one_change 展开成 PRD 草稿 |
| `/对比 [另一篇 paper]` | 对比两次 sensemaking 的认知 delta |

---

## 相关 Skill

| Skill | 关系 |
|-------|------|
| `skill-paper-discovery` | 上游：找到并推荐这篇 paper |
| `skill-user-profile` | 上游：建立用户 profile |
| `skill-visual-knowledge-design` | 下游：learning mechanism → slides |
| `skill-paper-to-prd` | 下游：one_change → PRD |

---

作者：Yi · 爱思考的伊伊子
[edu-ai-builders](https://github.com/edu-ai-builders) · 教育AI智造者
