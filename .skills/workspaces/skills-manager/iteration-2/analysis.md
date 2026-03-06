# Iteration-2 分析报告

## 总体结果（6 个 case 合并）

| Case | Prompt | Pass Rate | 路由方向 |
|------|--------|-----------|---------|
| 1 | 评估改进 pdf skill | 6/6 = 100% | ✅ eval-flow |
| 2 | 手动编辑后同步发布 | 5/5 = 100% | ✅ manage |
| 3 | 把经验沉淀成 skill | 6/7 ≈ 86% | ✅ create-flow |
| 4 | 找 PDF 表单填写 skill | 5/5 = 100% | ✅ find-search |
| 5 | 从 GitHub 导入 skill | 3/5 = 60% | ⚠️ find-import（有歧义风险）|
| 6 | 找替代或改改 skill | 0/3 = 0% | ❌ 歧义未处理 |

**整体 pass rate: 25/31 ≈ 81%**
**路由方向准确率: 4/6 = 67%**（Case 5 有风险，Case 6 不确定）

## 新发现的问题

### Issue A（High）：Routing 第 1 条缺少「导入」触发词

**位置：** 根 SKILL.md 第 95 行

**现状：** "用户要找 skill、下载 skill、更新外部 skill、查看上游信息"

**缺失：** "导入 skill"、"从 GitHub/URL 导入"——这些是用户说"导入"时的高频表达。"下载"在中文语境下偏指获取文件，"导入"偏指纳入管理体系，二者并不等价。

**风险：** LLM 可能将"导入外部 skill"理解为"在本地创建一个新 skill"，误入第 2 条。

**修复：** 第 1 条追加"导入 skill"。

### Issue B（High）：缺少多意图 / 歧义路由处理

**位置：** 根 SKILL.md Routing 章节

**现状：** "先判断用户属于哪一类场景"——只支持单意图匹配，没有歧义处理。

**风险：** 用户在一句话中混合多种意图时，LLM 会随机选一条路由，或违反"只读一个 reference"的约束。

**修复：** 在 Routing 末尾加歧义处理规则——当用户意图横跨多条路由时，先向用户确认。

### Issue C（Medium）：eval-flow 缺少路由型 skill 的覆盖指引

**位置：** creator/references/eval-flow.md

**现状：** "设计 2-3 个真实测试 prompt"——没有提示应覆盖所有路由分支。

**风险：** 评估者（包括 LLM 自身）可能只围绕当前改动设计 case，遗漏未改动的路由分支。这正是本次自举评估中发生的事。

**修复：** 在 eval-flow.md 中加一条提示：对路由型 skill，测试集应覆盖所有路由分支，包括歧义边界。

## 改进计划

1. 根 SKILL.md Routing 第 1 条追加「导入」触发词
2. 根 SKILL.md Routing 末尾加歧义处理规则
3. creator/references/eval-flow.md 加路由覆盖指引
