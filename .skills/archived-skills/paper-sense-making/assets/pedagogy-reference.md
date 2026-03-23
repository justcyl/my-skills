# Pedagogy Reference Library
**供 skill-paper-sensemaking 引用的教学法参考库**

---

## 核心教学法

### Scaffolding（脚手架）
- **理论来源**：Vygotsky ZPD，Wood, Bruner & Ross (1976)
- **核心逻辑**：在学习者当前能力和目标之间提供临时支撑，随能力提升逐渐撤除
- **学习循环**：任务超出能力 → 提供支架 → 学习者完成 → 撤除支架 → 内化
- **常见 UI 模式**：hint hierarchy（分级提示）、worked example（范例展示）、sentence starters
- **认知冲突触发点**：AI 直接给答案 ≠ scaffolding，scaffold 必须有撤除机制

### ZPD（最近发展区）
- **理论来源**：Vygotsky
- **核心逻辑**：学习发生在"独立完成"和"在帮助下完成"之间的区间
- **对 AI 设计的含义**：系统需要先评估学习者当前水平，再决定介入深度
- **常见误用**：把 ZPD 当成"给稍微难一点的题"，忽略了动态调整

### 认知学徒制（Cognitive Apprenticeship）
- **理论来源**：Collins, Brown & Newman (1989)
- **三阶段**：Modeling（示范）→ Coaching（指导）→ Fading（淡出）
- **关键**：专家思维过程必须外显化（think aloud），不能只展示结果
- **对 AI 设计的含义**：AI 应该展示推理过程，不只给答案

### 形成性评估（Formative Assessment）
- **理论来源**：Black & Wiliam (1998)
- **核心逻辑**：评估的目的是改进学习，不是测量结果
- **五个关键策略**：
  1. 明确学习目标
  2. 收集学习证据
  3. 给予前进性反馈（feedforward，不只是 feedback）
  4. 学生自评
  5. 同伴互评
- **对 AI 设计的含义**：反馈必须指向"下一步怎么做"，不只是"哪里错了"

### 概念转变（Conceptual Change）
- **理论来源**：Posner et al. (1982)，Chi (2008)
- **核心逻辑**：学习者有根深蒂固的 misconception，新知识必须主动替换旧概念
- **发生条件**：不满意现有概念 + 新概念可理解 + 可信 + 有用
- **对 AI 设计的含义**：系统需要先诊断 misconception，再设计替换路径

### Worked Examples（范例学习）
- **理论来源**：Sweller (1988)，认知负荷理论
- **核心逻辑**：看范例比自己解题学得更快（初学阶段）
- **效果边界**：随专业程度提升，worked example 效果下降（expertise reversal effect）
- **对 AI 设计的含义**：初学者看范例，熟练者自己做，系统需要判断学习者阶段

### 探究式学习（Inquiry-Based Learning）
- **理论来源**：Dewey，Bruner
- **核心逻辑**：学习者通过提问、假设、实验、反思来构建知识
- **对 AI 设计的含义**：AI 的角色是引发问题，不是提供答案；学习者是主动建构者

### Self-Explanation（自我解释）
- **理论来源**：Chi et al. (1989)
- **核心逻辑**：让学习者用自己的话解释，比反复阅读效果更好
- **对 AI 设计的含义**：设计"让学习者先解释"的交互，AI 再补充或纠正

### Retrieval Practice（提取练习）
- **理论来源**：Roediger & Karpicke (2006)
- **核心逻辑**：主动回忆比重复学习更能巩固记忆（测试效应）
- **对 AI 设计的含义**：间隔提问比持续提示更有效

---

## 教学法检测信号

读 paper 时，用这些信号判断背后的教学法：

| 信号 | 可能的教学法 |
|------|-------------|
| 系统根据学习者表现调整难度 | Scaffolding / ZPD |
| AI 展示推理过程 | 认知学徒制 |
| 反馈指向"下一步" | 形成性评估 |
| 系统先诊断 misconception | 概念转变 |
| 学习者先看范例再做题 | Worked Examples |
| 学习者提问驱动学习 | 探究式学习 |
| 学习者被要求解释自己的答案 | Self-Explanation |
| 间隔测试 | Retrieval Practice |
| 没有明显教学法 | 需要标注：pedagogy implicit / absent |
