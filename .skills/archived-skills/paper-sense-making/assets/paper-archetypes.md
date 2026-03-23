# Paper Archetypes
**论文类型分类 · 每种类型的 sensemaking 重点**

---

## 五种类型

### Learning Science
**识别信号：** 以学习理论为框架，研究认知过程、学习机制、记忆、迁移  
**Sensemaking 重点：**
- 学习机制（学习是怎么发生的）
- 教学法的理论依据
- 对学习者认知过程的假设

**常见问题：** 理论很好，但缺乏 AI 实现路径  
**对 builder 的价值：** 提供设计原则，不提供系统设计

---

### AI System Paper
**识别信号：** 介绍一个 AI/ML 系统，有 model、dataset、evaluation  
**Sensemaking 重点：**
- System pipeline（输入→处理→输出）
- 学习者交互设计
- 有没有真正的 learning mechanism，还是只是 prediction

**常见问题：** 把 accuracy 提升当成"学习效果"，忽略教学法  
**对 builder 的价值：** 提供技术实现参考，但需要补充教学法层

---

### EdTech Design Paper
**识别信号：** 设计并评估一个教育技术工具，有 user study  
**Sensemaking 重点：**
- Pedagogy + interaction design 的结合
- 学习者行为数据
- 老师的角色

**常见问题：** 工具设计合理，但学习效果测量不严谨  
**对 builder 的价值：** 最直接的参考，可以直接提取 interaction pattern

---

### Empirical Study
**识别信号：** RCT、准实验、survey，有统计分析，研究"A 是否比 B 有效"  
**Sensemaking 重点：**
- Effect size（不只是 p value）
- 实验条件是否真实（ecological validity）
- 结论的适用边界

**常见问题：** 结论被过度泛化，条件限制被忽略  
**对 builder 的价值：** 提供"什么有效"的证据，但需要自己判断是否适用于自己的场景

---

### Theory / Review
**识别信号：** 综述、元分析、理论框架，没有原始实验数据  
**Sensemaking 重点：**
- 框架的结构和逻辑
- 覆盖了哪些 / 没有覆盖哪些
- 对实践的指导意义

**常见问题：** 框架太抽象，难以直接用于产品设计  
**对 builder 的价值：** 提供 mental model，适合建立领域认知，不适合直接 copy

---

## 类型组合

大部分 paper 是混合类型：

| 组合 | 描述 |
|------|------|
| AI System + EdTech Design | 设计了一个 AI 工具并做了 user study |
| Learning Science + Empirical | 用实验验证了一个学习理论 |
| EdTech Design + Theory | 基于某个教学理论设计工具，没有严格实验 |

遇到混合类型，标注为 `Mixed`，在 `paper_type_reason` 里说明主导类型。
