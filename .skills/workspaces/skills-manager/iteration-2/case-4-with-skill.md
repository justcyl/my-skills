# Eval Case 4: 路由推理 — "有没有处理 PDF 表单填写的 skill？帮我找一个"

## With-Skill 推理

LLM 读到根 SKILL.md 的 Routing：

1. 检查第 1 条："**找 skill**、下载 skill、更新外部 skill、查看上游信息" — **命中**。"有没有…帮我找一个" = 找 skill
2. 无需继续检查第 2、3 条
3. 操作：读 `references/scene-find-and-import.md`
4. 进入后，scene-find-and-import.md Mode Selection：匹配"仅搜索"模式
5. 使用 `bash scripts/find_or_import_skill.sh search <query>`

**最终路由：** references/scene-find-and-import.md → 搜索模式 ✅

## 逐条 Expectation 判定

| # | Expectation | Passed | Evidence |
|---|------------|--------|----------|
| 1 | 识别为「找 skill」场景，匹配 Routing 第 1 条 | ✅ | 第 95 行 "找 skill" 直接命中 |
| 2 | 读取 references/scene-find-and-import.md | ✅ | 第 96 行指令明确 |
| 3 | 不读取 references/scene-create-skill.md | ✅ | 用户没有任何创建/评测意图 |
| 4 | 不进入 creator/SKILL.md | ✅ | 第 1 条流程不涉及 creator |
| 5 | 使用 find_or_import_skill.sh search | ✅ | Workflow 1.2 明确；scene-find-and-import.md Search Workflow 也确认 |

**Pass rate: 5/5 = 100%**

## 发现的问题

无。第 1 条触发话术直接覆盖。
