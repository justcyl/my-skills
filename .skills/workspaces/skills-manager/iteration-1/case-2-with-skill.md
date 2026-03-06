# Eval Case 2: 路由推理 — "我手动改了 translator skill 的 SKILL.md，帮我同步一下状态然后发布"

## With-Skill 推理

LLM 读到根 SKILL.md 的 Routing 章节：

1. 检查第 1 条："找 skill、下载 skill、更新外部 skill、查看上游信息" — 不匹配（不是找/下载/更新外部）
2. 检查第 2 条："创建新 skill、重建 skill 骨架、评测 skill、评估改进 skill 或优化 description" — 不匹配（不是创建/评测/优化 description）
3. 检查第 3 条："**同步状态、处理手动编辑**、分发、查询状态、归档或发布" — **命中**。"手动改了" + "同步" + "发布" 三个关键词全部对应
4. 操作：读 `references/scene-manage-skills.md`
5. Workflow 第 3 节进一步确认：手动编辑后的状态刷新与审计 → `finalize_manual_edits.sh`

**最终路由：** references/scene-manage-skills.md ✅

## 逐条 Expectation 判定

| # | Expectation | Passed | Evidence |
|---|------------|--------|----------|
| 1 | 识别为「手动编辑后同步」场景，匹配 Routing 第 3 条 | ✅ | "同步状态、处理手动编辑" 在第 105 行明确出现 |
| 2 | 读取 references/scene-manage-skills.md | ✅ | Routing 第 3 条指令明确 |
| 3 | 不读取 references/scene-create-skill.md | ✅ | 用户意图不匹配第 2 条任何关键词 |
| 4 | 不进入 creator/SKILL.md | ✅ | 第 3 条的处理链中不涉及 creator |
| 5 | 最终调用 finalize_manual_edits.sh | ✅ | Workflow 3.2 明确指出 |

**Pass rate: 5/5 = 100%**

## 发现的问题

无路由问题。第 3 条的触发话术已经覆盖了"手动编辑 + 同步 + 发布"的组合。
