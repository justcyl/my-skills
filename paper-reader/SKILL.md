---
name: paper-reader
description: 辅助精读 AI/NLP 学术论文。逐节分析引言挖坑结构、相关工作踩人写法、图表叙事逻辑、实验设计思路与结论收尾。当用户说「帮我读这篇论文」「分析一下这篇paper的引言」「这个相关工作怎么写的」「帮我看看实验部分」「这篇paper的contribution是什么」「怎么学这篇paper的写法」时触发。
---

# Paper Reader

辅助用户精读 AI/NLP 学术论文。重点不是"复述内容"，而是**拆解写作结构、提炼可复用的写法模式**。

## When To Use

- 用户丢了一篇论文，想理解它在做什么
- 用户想学某一节（引言、相关工作、实验……）的写法
- 用户想知道这篇论文的 contribution 怎么组织的
- 用户在写自己的论文，想参考同类工作的结构

## Routing

根据用户关注的部分，按需读取对应 reference：

| 用户关注 | 加载 |
|---|---|
| 引言 / introduction | `references/introduction.md` |
| 相关工作 / related work | `references/related-work.md` |
| 图和表 | `references/figures-tables.md` |
| 实验 / experiments / results | `references/experiments.md` |
| 结论 / conclusion / limitation | `references/conclusion.md` |
| 整篇 / 通读 | 按顺序加载所有 reference |

不需要一次性把所有 reference 全部读完。

## Default Behavior

1. 先识别用户最关注哪一节，或者是否要通读
2. 加载对应 reference，按其指引展开分析
3. **每一节都先给出结构分析，再给出写法点评**
   - 结构分析：这篇论文在这一节是怎么组织的
   - 写法点评：哪些写法值得学，哪些地方可以更好
4. 结尾给一个「可直接复用的模式」总结，方便用户写自己的论文时参考

## Output Style

- 分节呈现，标题清晰
- 用引用块（`>`）摘录论文原文中的关键句
- 用列表呈现"写法模式"，让用户一眼看到可复用的东西
- 不堆砌术语，说人话
- 如果用户只想快速了解，先给 TL;DR，再展开
