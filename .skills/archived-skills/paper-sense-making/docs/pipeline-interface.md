# Pipeline Interface Spec
**与上下游 skill 的接口规范 · v2**

---

## 上游接口

### 来自 skill-paper-discovery

```
/sensemaking
profile: [用户 profile 自然语言]
recommendation_reason: [为什么推荐这篇，可选]

[论文全文]
```

`recommendation_reason` 可选。有了它，AI 生成认知冲突时可以参考"为什么选中这篇"，让冲突更有针对性。

### 来自 skill-user-profile

如果上游有结构化 profile，转换为自然语言传入即可。**不要**直接传 JSON 结构——sensemaking 需要从自然语言里推断隐含假设，结构化字段只暴露显式知识。

---

## 下游接口

### 输出给 skill-paper-to-prd

触发方式：三幕对话完成后，用户发送 `/prd`

传入字段：
```json
{
  "profile_read": "...",
  "act3_reconstruction": {
    "one_change": "用户说打算在项目里改变的一件事"
  }
}
```

`one_change` 是 PRD 的起点。`/prd` 指令把它展开成完整 feature spec。

### 输出给 skill-visual-knowledge-design

触发方式：三幕对话完成后，用户发送 `/可视化`

传入字段：
```json
{
  "act1_comprehension": {
    "learning_mechanism": "学习者做什么 → 系统响应 → 学习者变化"
  }
}
```

`learning_mechanism` 是 visual knowledge design 的输入素材。

---

## 完整 JSON Schema（v2）

```typescript
interface SensemakingOutput {
  meta: {
    paper_title: string           // 从原文提取
    profile_read: string          // AI 对用户 profile 的一句话复述
    session_date: string          // YYYY-MM-DD
  }

  act1_comprehension: {
    core_claim: string            // 核心主张，直接写内容，不用"论文认为"
    learning_mechanism: string    // 箭头格式：学习者做什么 → 系统响应 → 学习者变化
    user_perspective: string      // 这篇 paper 和用户当前项目的具体关联
  }

  act2_collision: {
    user_schema_before: string    // 用户在对话里暴露的原有隐含假设
    paper_challenge: string       // paper 挑战这个假设的核心发现（直接写内容）
    friction: string              // 为什么这两个认知不能同时成立
    user_stance: 'agree' | 'unsure' | 'disagree'
    user_reasoning: string        // 用户表态时说的话，尽量用他们自己的语言
    probe_exchange: Array<{
      probe: string               // AI 追问的内容
      response: string            // 用户的回答
    }>
  }

  act3_reconstruction: {
    before: string                // 用户进来时的认知假设（从对话提取）
    after: string                 // 对话结束时用户自己说的新理解
    delta: string                 // AI 总结：认知变化的核心是什么
    one_change: string            // 用户说打算在项目里改变的一件事
  }
}
```

---

## v1 → v2 字段变化

**移除的字段：**

| v1 字段 | 移除原因 |
|---------|---------|
| `paper_type` / `paper_type_reason` | 属于 comprehension，不是 sensemaking |
| `relevance` | 应由 discovery skill 在推荐时评估，不在分析时重复 |
| `claims` | 合并进 `act1_comprehension.core_claim` |
| `learning_loop` | 简化为 `act1_comprehension.learning_mechanism` |
| `pedagogy` | 移除，AI 内部参考即可，不暴露给用户 |
| `system_pipeline` | 移除 |
| `human_roles` | 移除 |
| `conflicts[]` | 重构为 `act2_collision`，加入用户表态和追问记录 |
| `no_conflict_note` | 合并进 `act2_collision` 的对话处理 |
| `productization` | 移至下游 `skill-paper-to-prd` |
| `decisions` | 移除，由 `one_change` 替代（更具体，来自用户而非 AI） |
| `open_questions` | 移除，由对话中的 probe 替代 |
| `takeaway` | 重构为 `act3_reconstruction.delta`（AI）+ `after`（用户自己的话） |

**新增的字段：**

| v2 字段 | 说明 |
|---------|------|
| `meta.session_date` | 便于 schema tracking 和多次 sensemaking 对比 |
| `act2_collision.friction` | 明确两个认知不能同时成立的原因 |
| `act2_collision.user_stance` | 记录用户的表态结果 |
| `act2_collision.user_reasoning` | 保留用户自己的语言，不被 AI 替换 |
| `act2_collision.probe_exchange[]` | 记录完整追问过程，可用于 schema tracking |
| `act3_reconstruction.delta` | AI 对认知变化的总结（区别于用户自己说的 `after`） |
