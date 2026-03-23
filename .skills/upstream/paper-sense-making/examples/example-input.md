# 示例输入
**Example Input · skill-paper-sensemaking v2**

---

## 基本格式

```
/sensemaking
profile: [用户的自然语言描述，不需要结构化，一句话到几句话都可以]

[论文全文直接粘贴]
```

触发后，AI 会引导你走过三幕对话。整个过程大约 10-20 分钟，需要你回应 AI 的问题。

---

## 示例 A：EdTech 创业者 × Vibe Researching paper

```
/sensemaking
profile: EdTech 创业者兼教育学博士，正在构建 edu-ai-builders skill pipeline，
核心 mission 是把 AI 和学习科学结合，帮助教育工作者和研究者更有效地使用 AI。
熟悉 scaffolding、ZPD、认知负荷等学习科学框架，正在做 skill-paper-sensemaking
这个工具，目标用户是教育研究者和 EdTech builder。

[粘贴 Vibe Researching as Wolf Coming 全文]
```

**AI 会推断的 existing schema：**
- skill pipeline = 帮用户做得更快更好
- AI 工具的价值 = 降低执行门槛，让更多人能做更多事
- 用户的认知能力不会因为用了 AI 而退化

**可能的冲突点：**
Zhang (2026) 的核心发现是：delegation boundary 是认知维度的，不是阶段维度的。
每个 pipeline 阶段里都有可以授权的任务和不能授权的任务，
而过度授权会造成 verification gap——用户如果从没做过这件事，
就无法判断 AI 做得对不对。
对于正在构建 skill pipeline 的 EdTech 创业者来说，这是一个直接的挑战：
你的 skill 是在帮用户增强能力，还是在帮用户跳过需要培养的能力？

---

## 示例 B：初中数学老师

```
/sensemaking
profile: 初中数学老师，正在设计一个让学生练习几何证明的工具。
学生总是抄答案或完全放弃，我想用 AI 在思考过程中给提示，
而不是直接给答案。了解 scaffolding 概念，不清楚怎么用 AI 实现。

[论文全文]
```

**AI 会推断的 existing schema：**
- 提示 = 给一个 hint 让学生往下做
- AI 的角色 = 更聪明的答案提供者
- 只要不直接给答案就是好的 scaffold

---

## 示例 C：教育学博士生

```
/sensemaking
profile: 教育学 PhD，研究方向是 formative assessment 在 AI 时代的变化。
读这篇 paper 是为了找 literature gap，看现有研究在 AI feedback 的
学习机制上还没研究清楚什么。对这个领域比较熟悉。

[论文全文]
```

**AI 会推断的 existing schema：**
- formative assessment 的核心机制（feedback 的时机、形式、学习者响应）是稳定的
- AI 改变的是 feedback 的效率，不是 feedback 的教学逻辑
- 研究 AI feedback 只需要把已有框架应用到新工具上

---

## 注意：v2 是对话式的

v2 触发后，AI 不会一次性输出所有内容。它会：
1. 输出幕一（理解），然后 **等你回应**
2. 进入幕二（冲突），要求你 **表态**，然后根据你的回答追问
3. 幕三（重构）之后，输出完整 JSON

整个过程是一个真实的对话，不是报告生成。
