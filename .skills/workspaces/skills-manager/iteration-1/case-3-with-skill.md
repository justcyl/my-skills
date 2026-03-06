# Eval Case 3: 路由推理 — "我想把之前写代码时常用的一些模式沉淀成一个 skill"

## With-Skill 推理

LLM 读到根 SKILL.md 的 Routing 章节：

1. 检查第 1 条："找 skill、下载 skill、更新外部 skill、查看上游信息" — 不匹配
2. 检查第 2 条："**创建新 skill**、重建 skill 骨架、评测 skill、评估改进 skill 或优化 description" — **命中**。"沉淀成一个 skill" = 创建新 skill
3. 操作：读 `references/scene-create-skill.md`
4. 根 SKILL.md 第 102 行已暴露子路由："新建 / 重写 skill → creator 读 creator/references/create-flow.md"
5. 进入 scene-create-skill.md 后，第 20-22 行：目标 skill 还不存在 → 先运行 create_skill.sh → 然后进入 creator
6. 进入 creator/SKILL.md 的 Routing 第 1 条："用户要新建 skill、重写 skill 结构、把经验沉淀成 skill → 读 references/create-flow.md"

**最终路由：** creator/references/create-flow.md ✅

## 逐条 Expectation 判定

| # | Expectation | Passed | Evidence |
|---|------------|--------|----------|
| 1 | 识别为「创建新 skill」场景，匹配 Routing 第 2 条 | ✅ | "创建新 skill" 在第 98 行出现，"沉淀"意图明确映射 |
| 2 | 读取 references/scene-create-skill.md | ✅ | Routing 第 2 条指令明确 |
| 3 | 判断目标 skill 不存在，需要先运行 create_skill.sh | ⚠️ | scene-create-skill.md 第 20-22 行有指引，但**根 SKILL.md 自身不足以判断**——它只在 Workflow 2.2 说"如果目标 skill 尚不存在"，并没有告诉 LLM 如何判断 skill 是否存在 |
| 4 | 进入 creator/SKILL.md | ✅ | scene-create-skill.md 和根 SKILL.md 都指向 creator |
| 5 | creator 内部路由到 references/create-flow.md | ✅ | 根 SKILL.md 第 102 行暴露了子路由；creator Routing 第 1 条也确认 |
| 6 | 开始需求访谈（Capture Intent），而非直接跑评测 | ✅ | create-flow 的默认流程是 capture → interview → write |

**Pass rate: 5.5/6 ≈ 92%**（第 3 条部分通过——路由方向正确，但判断 skill 是否存在的方法未在根 SKILL.md 中说明）

## 发现的问题

**问题 1：如何判断 skill 是否存在？**

根 SKILL.md Workflow 2.2 说"如果目标 skill 尚不存在，先用 create_skill.sh"，但没有告诉 LLM 用什么方式判断 skill 是否存在。可能的判断方式：
- 检查 `my-skills/<skill-id>/` 目录是否存在
- 查 `.skills/registry.json`
- 用户自己说了

这不是路由问题，但会影响执行正确性。建议在 Workflow 2.2 或 scene-create-skill.md 中补充判断方法。

**问题 2：「沉淀」这个词**

根 SKILL.md 第 98 行的触发话术中没有"沉淀"。但 creator/SKILL.md Routing 第 1 条有"把经验沉淀成 skill"。由于"创建新 skill"已经足够覆盖语义，这不是一个严重问题，但如果想更稳健，可以在根 SKILL.md 补上"把经验沉淀成 skill"。
