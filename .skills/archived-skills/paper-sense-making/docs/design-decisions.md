# Design Decisions
**skill-paper-sensemaking 的设计决策记录**

---

## 决策 1：Profile 用自然语言，不用结构化字段

**背景：** 考虑过用固定字段（角色、领域、当前项目、熟悉的教学法）来结构化 profile。

**问题：** 结构化 profile 只暴露用户说自己知道什么，而 sensemaking 需要的是推断用户**没有意识到自己相信**的假设（existing schema）。这两者是不同的。

**决策：** Profile 用自然语言。AI 从中推断 existing schema，用这个隐含假设生成认知冲突。

---

## 决策 2：认知冲突必须基于推断的 schema，不能强行制造

**背景：** 某篇 paper 对某个用户可能完全没有新东西。

**问题：** 强行生成冲突会让输出失去信任度。

**决策：** 如果真的没有冲突，诚实说明。这本身也是有价值的信息——说明用户的认知已经很准确，或者这篇 paper 对他们来说太简单了。

---

## 决策 3：从一次性输出改为三幕对话（v1 → v2 核心变化）

**背景：** v1 是一次性输出，profile + paper 进来，所有结果（10+ 字段的 JSON）一次性出去。Canvas 是主要交互界面。

**问题：** 用户"看到了"但没有"改变"。Canvas 是阅读界面，不是认知操作界面。Sensemaking 的本质是一个过程，不是一个输出。

**决策：** 整个 sensemaking 分三幕在对话中完成：
- 幕一（理解）：AI 输出理解 + probe，等用户确认
- 幕二（冲突）：AI 暴露摩擦 + 要求用户表态，根据回答条件式追问
- 幕三（重构）：AI 总结认知 delta，收集用户的 one change，输出 JSON

所有交互在 AI 对话中完成。Canvas 只接收最终 JSON，只读展示。

**代价：** 用户需要投入更多时间完成一次 sensemaking。这是有意为之的——认知重构需要摩擦。

---

## 决策 4：不假设用户会提出好问题，AI 主动 probe

**背景：** v1 在输出后列出"后续指令"（`/深挖`、`/产品`等），等用户主动触发。

**问题：** 大多数用户不会主动提出深度追问。Sensemaking 需要外力推动，不能依赖用户的自驱力。

**决策：** AI 在每幕结束后主动给出具体的 probe 问题，不等用户主动发问。幕二的追问是条件式的——根据用户的表态（同意/不确定/不同意）走不同的追问路径。

---

## 决策 5：Canvas 删除论文原文左栏，变为纯认知轨迹展示

**背景：** v1 Canvas 左侧显示论文原文，右侧显示分析结果，类似阅读器界面。

**问题：** 左侧论文原文没有 traceability（无法高亮对应分析来源），占据大量空间，但没有提供实质价值。Canvas 的核心价值不是"读论文"，而是"看到认知变化轨迹"。

**决策：** 删除左栏。Canvas 变为单列，完整展示三幕认知流：理解 → 冲突（before/after 双列对比）→ 重构（before/after + delta + one change）。如果未来要加 traceability，作为独立功能重新设计，不混在当前 Canvas 里。

---

## 决策 6：移除产品化相关字段（productization、decisions、open_questions）

**背景：** v1 JSON 包含 `productization`（feature seed、interaction pattern、teachable logic）、`decisions`（do/pause/rethink）、`open_questions` 等字段。

**问题：** 这些字段回答的是"这个 paper 能做什么产品"，属于 comprehension + productization，不是 sensemaking。它们分散了注意力，让 Canvas 变成了一个大而全的分析报告，而不是认知重构的载体。

**决策：** 完全移除这些字段。产品化提取交由下游 skill（`skill-paper-to-prd`）通过 `/prd` 指令处理。Sensemaking skill 只专注认知重构。

---

## 决策 7：信息茧房问题不在本 skill 里解决

**背景：** 如果 profile 是静态的，discovery skill 推荐的 paper 会越来越符合用户已有认知，sensemaking 的冲突会越来越少。

**决策：** 这个问题属于 `skill-paper-discovery` 的职责范围。Sensemaking skill 只负责分析已经选定的 paper，不参与推荐逻辑。

---

## 版本历史

| 版本 | 核心变化 |
|------|---------|
| v0.1 | 对话式引导，苏格拉底式提问，两阶段（读前/读后） |
| v0.2 | Pipeline 节点，一次性输入输出，profile 用自然语言，10+ 字段 JSON |
| v1.0 | Canvas 双栏（论文原文 + 分析结果），canvas 有简单交互 |
| v2.0 | 三幕对话式，AI 主动 probe，Canvas 只读单列，聚焦认知重构，移除产品化字段 |

---

## 待解决

- [ ] 多篇 paper 对比 sensemaking（`/对比` 指令的完整实现）
- [ ] Profile 随 sensemaking 次数积累的演化机制（schema tracking）
- [ ] 与 `skill-paper-discovery` 的 anti-echo-chamber 对接
- [ ] Canvas traceability：高亮分析结论对应的 paper 原文段落
- [ ] example-output.json 替换为 v2 真实对话结果
