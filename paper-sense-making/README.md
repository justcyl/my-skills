# skill-paper-sensemaking

**论文意义建构 · Paper Sensemaking Skill**

> 不是摘要，不是解读，是认知重构。

---

## 为什么普通的"AI 读论文"不够

市面上大多数 AI 读论文工具做的事情是：

```
paper → summary / explanation
```

更好一点的工具会做：

```
paper → key findings + implications
```

这些都解决了"理解"的问题，但没有解决"改变"的问题。

**理解 ≠ Sensemaking。**

| | 理解（Comprehension） | Sensemaking（意义建构） |
|---|---|---|
| 核心问题 | 这篇 paper 说了什么？ | 这篇 paper 改变了我怎么看一件事？ |
| 认知操作 | 接收信息 | 重构框架 |
| 结果 | 我知道了 X | 我原来以为 X，现在我认为 X' |
| 学习发生在 | 读完之后 | 冲突发生时 |
| 用户角色 | 被动接收 | 主动表态 |

普通的"AI 解读论文"工具，哪怕做得再好，用户读完最多是"涨知识了"。认知框架没有被挑战，也就没有被更新。

---

## 这个 Skill 做什么

核心流程：

```
paper × 你是谁 → 找到摩擦点 → 你被迫表态 → 认知重构 → 可视化轨迹
```

关键词是**摩擦**。Sensemaking 不是帮你读懂 paper，而是找到 paper 和你现有认知框架之间的张力，然后把你推进这个张力里，让你不得不重新想清楚自己的立场。

这个 skill 做三件事：

**幕一：帮你读懂**
提取核心主张、学习机制，并从你的具体背景解读这篇 paper 对你意味着什么。不是泛泛的"这对教育很有价值"，而是"你正在做 X，这篇 paper 直接挑战了你在 X 里的假设 Y"。

**幕二：制造冲突**
从你的 profile 推断你没有说出来但一定相信的东西（existing schema），找到 paper 里最挑战这个 schema 的发现，呈现摩擦。然后要求你表态：你同意 paper 的说法吗？根据你的回答，继续追问，直到你的立场和理由变得清晰。

**幕三：固化重构**
把对话里发生的认知变化用你自己的语言说出来：你进来时的假设是什么，现在的理解是什么，改变了什么。最后问你：基于这个新认知，你打算在项目里改变一件什么事。

对话结束后输出完整 JSON，在 Canvas 里可视化完整认知轨迹。

---

## 和普通 Explanation Skill 的对比

假设用户是一个初中数学老师，正在做 proof 反馈工具，读了一篇关于 scaffolding 和 AI feedback 的 paper。

**普通 explanation skill 的输出：**

> 这篇 paper 研究了 AI 即时反馈对学习者自我诊断能力的影响。研究者发现，即时纠正性反馈能减少错误，但同时削弱了学习者的自我调节能力。作者建议在 AI 设计中引入"延迟反馈"机制，给学习者自己思考的空间。对于教育工作者来说，这意味着……

用户读完：明白了。有意思。（然后继续做原来的工具）

**这个 skill 的对话：**

> **AI（幕二）：** 你在做的反馈工具，核心假设应该是：给学习者提示 = 帮助学习。这篇 paper 发现的是：没有撤除计划的 hint 不是脚手架，而是认知拐杖——学生学会等待提示，而不是主动思考。这两个认知不能同时成立：如果你相信"给提示=帮助"，你就不会设计撤除机制；但如果 paper 是对的，不设计撤除机制的工具会训练出依赖 AI 的学生。你现在怎么看这个冲突？
>
> **用户：** 我觉得有道理，但我不确定"撤除"在 AI 工具里怎么实现……
>
> **AI：** 你不确定的是"撤除"的实现方式，还是你认为"撤除"这件事本身在你的场景里不适用？
>
> **用户：** 是实现方式。我觉得撤除是对的，但如果学生一直卡住怎么办？
>
> **AI：** 好。所以你其实已经接受了"hint 需要有撤除设计"，问题是边界条件：学生卡多久之后 AI 才应该介入？这个边界的设计，就是你工具的核心教学决策……

用户对话完：我的工具需要一个"等待阈值"设计，学生卡住 N 分钟后才给 hint，而不是即时响应。这是一件具体的事，我知道我要做什么。

---

## 为什么要"对话完成后"才出 JSON

这不是技术限制，是设计决策。

JSON 是认知轨迹的**沉淀**，不是分析报告。它记录的是对话里真实发生的事——用户原本的假设、用户自己说的新理解、用户承诺要改变的一件事。这些内容只有在对话完成之后才存在。

如果在对话开始前就输出 JSON，那输出的只是 AI 对用户的猜测，不是用户真实的认知重构。Canvas 展示的是"你的认知变化轨迹"，不是"AI 对这篇 paper 的分析"。

---

## 快速开始

### Step 1：配置 system prompt

将 `prompt/system-prompt.md` 的内容注入到：
- Claude Project 的 system prompt
- OpenClaw skill 配置
- 任何支持 system prompt 的 AI 环境

### Step 2：触发对话

```
/sensemaking
profile: 初中数学老师，正在设计几何 proof 的反馈工具，熟悉 scaffolding，不熟悉 LLM

[粘贴论文全文]
```

一句话 profile 也可以：

```
/sensemaking
profile: EdTech 创业者，做 AI 教育内容，熟悉 learning sciences

[论文全文]
```

### Step 3：完成三幕对话

AI 会引导你走过三幕。每幕结束后回应 AI 的问题，不需要提前准备什么。整个过程大约 10-20 分钟。

### Step 4：渲染 Canvas

对话结束后 AI 输出完整 JSON → 打开 `artifact/sensemaking-canvas.html` → 粘贴 JSON → 点"渲染认知轨迹"

Canvas 展示你的完整认知轨迹：你读之前的假设、paper 的挑战、你的立场、追问过程、认知 delta、你打算改变的一件事。

---

## 文件结构

```
skill-paper-sensemaking/
│
├── SKILL.md                           ← skill 类型、使用方式、接口摘要
├── README.md                          ← 你在这里
│
├── prompt/
│   └── system-prompt.md               ← 注入 AI 环境的完整 system prompt
│
├── artifact/
│   └── sensemaking-canvas.html        ← 只读 canvas，粘贴 JSON 渲染认知轨迹
│
├── assets/
│   ├── pedagogy-reference.md          ← 9 种教学法参考库（AI 内部参考）
│   └── paper-archetypes.md            ← 5 种论文类型与分析重点（AI 内部参考）
│
├── examples/
│   ├── example-input.md               ← 触发示例（多种 profile 场景）
│   └── example-output.json            ← 完整示例 JSON（真实对话结果）
│
└── docs/
    ├── design-decisions.md            ← 设计决策记录（为什么这样设计）
    └── pipeline-interface.md          ← JSON schema + 上下游接口规范
```

---

## 在 Pipeline 里的位置

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
- 用户 profile 已知（一句话自然语言，不需要结构化）
- Paper 已选定（paste 全文或摘要）

**不做的事：**
- 不推荐 paper（上游 `skill-paper-discovery` 的职责）
- 不做产品化提取（下游 `skill-paper-to-prd` 的职责）
- 不问用户是谁（profile 随触发指令一起传入）

---

## 后续指令（对话完成后）

| 指令 | 作用 |
|------|------|
| `/深挖 [冲突点]` | 苏格拉底式继续追问某个认知冲突 |
| `/prd` | 把 one_change 展开成完整 PRD 草稿 |
| `/可视化` | 把 learning mechanism 转为 slides 素材 |
| `/对比 [另一篇 paper]` | 对比两次 sensemaking 的认知 delta |

---

## L 等级

**L2** — 多步骤 workflow，人在循环中

AI 引导 → 用户回应 → AI 追问 → 用户深入 → AI 总结 → JSON 输出 → Canvas 渲染

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
