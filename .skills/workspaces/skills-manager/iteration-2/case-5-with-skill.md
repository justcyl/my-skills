# Eval Case 5: 路由推理 — "把 github.com/anthropics/courses 这个仓库里的 prompt-engineering skill 导入进来"

## With-Skill 推理

LLM 读到根 SKILL.md 的 Routing：

1. 检查第 1 条："找 skill、**下载 skill**、更新外部 skill、查看上游信息" — **命中**。用户给了 GitHub URL 要导入 = 下载 skill
2. ⚠️ **潜在歧义点**：第 1 条说"下载 skill"，但用户说的是"导入"。第 1 条没有"导入"这个词。
   - 但 scene-find-and-import.md 的文件名包含 "import"
   - Workflow 1.3 说"选定来源后，用 find_or_import_skill.sh import"
   - 第 97 行补充说明："该模块已吸收原 find-skills 的触发话术、搜索呈现与**导入决策流程**"
   - 综合判断：LLM 大概率能正确路由，但"导入"这个核心词缺失于第 1 条的触发话术是一个弱点
3. 操作：读 `references/scene-find-and-import.md`
4. 进入后，Mode Selection：匹配"直接导入"模式（用户已给 URL）
5. 使用 `bash scripts/find_or_import_skill.sh import <source>`

**最终路由：** references/scene-find-and-import.md → 直接导入模式 ✅（但有弱点）

## 逐条 Expectation 判定

| # | Expectation | Passed | Evidence |
|---|------------|--------|----------|
| 1 | 识别为「导入外部 skill」场景，匹配 Routing 第 1 条 | ⚠️ | "下载 skill" 可覆盖，但第 1 条触发话术缺少"导入"一词。第 97 行补充说明中有"导入决策流程"但这是描述而非触发词 |
| 2 | 读取 references/scene-find-and-import.md | ✅ | 第 96 行指令明确 |
| 3 | 不误判为「创建新 skill」 | ⚠️ | 大概率不误判，但存在风险——用户在说"把…skill 导入"，第 2 条有"创建新 skill"。如果 LLM 理解为"把外部内容变成本地新 skill" → 可能误入第 2 条。关键区分在于：用户给了明确的外部 URL，这更像"下载"而非"创建" |
| 4 | 使用 find_or_import_skill.sh import | ✅ | Workflow 1.3 和 scene-find-and-import.md Import Workflow 都确认 |
| 5 | 导入后执行审计与中文优化 | ✅ | Workflow 1.4-1.5 和 scene-find-and-import.md Audit And Refinement 都确认 |

**Pass rate: 3/5 + 2×0.5 = 4/5 = 80%**

## 发现的问题

**Issue（Medium）：Routing 第 1 条缺少「导入」触发词**

第 1 条写的是："用户要找 skill、下载 skill、更新外部 skill、查看上游信息"

但「导入 skill」「导入外部 skill」「从 GitHub 导入」这类高频用户话术不在其中。"下载"和"导入"在 LLM 理解中相近但不完全等价——"下载"偏被动获取，"导入"偏主动纳入。

更关键的是，第 2 条的"创建新 skill"可能与"导入"产生歧义：导入外部 skill 到本地，从某种角度看也是在本地"创建"了一个新的 skill 条目。

**建议修复：** 在第 1 条触发词中明确加入"导入 skill"或"导入外部 skill"。
