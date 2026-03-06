# Eval Case 1: 路由推理 — "帮我评估改进一下 pdf 这个 skill，上次测试及格率太低了"

## With-Skill 推理

LLM 读到根 SKILL.md 的 Routing 章节：

1. 检查第 1 条："找 skill、下载 skill、更新外部 skill、查看上游信息" — 不匹配
2. 检查第 2 条："创建新 skill、重建 skill 骨架、评测 skill、**评估改进 skill**" — **命中**。"评估改进"四个字直接出现在触发话术中
3. 操作：读 `references/scene-create-skill.md`
4. 根 SKILL.md 已暴露 creator 子路由：
   - "评测 / 评估改进 / 迭代修订" → creator 读 `creator/references/eval-flow.md`
   - LLM 可以直接判断这是 eval-flow 而非 create-flow
5. 进入 scene-create-skill.md 后，第 25 行："用户只要评测、benchmark、viewer 审阅或 description 优化 → 直接进入 creator/SKILL.md"
6. 进入 creator/SKILL.md 的 Routing 第 2 条："用户要跑测试集、benchmark、viewer 审阅、盲评或迭代修订 → 读 references/eval-flow.md"

**最终路由：** creator/references/eval-flow.md ✅

## 逐条 Expectation 判定

| # | Expectation | Passed | Evidence |
|---|------------|--------|----------|
| 1 | 识别为「评估改进」场景，匹配 Routing 第 2 条 | ✅ | "评估改进 skill" 在第 98 行明确出现 |
| 2 | 读取 references/scene-create-skill.md | ✅ | Routing 第 2 条指令明确 |
| 3 | 判断 pdf skill 已存在，不运行 create_skill.sh | ✅ | scene-create-skill.md 第 25-26 行：已存在且只要评测 → 直接进 creator |
| 4 | 进入 creator/SKILL.md | ✅ | scene-create-skill.md 第 25-26 行 |
| 5 | creator 内部路由到 references/eval-flow.md 而非 create-flow.md | ✅ | 根 SKILL.md 第 103 行已暴露子路由；creator Routing 第 2 条也确认 |
| 6 | 不会误路由到 scene-manage-skills.md | ✅ | "同步状态、处理手动编辑" 与用户意图不匹配 |

**Pass rate: 6/6 = 100%**

## 发现的问题

无明显路由问题。刚修改的第 98 行和第 103 行正好覆盖了这个 case。
