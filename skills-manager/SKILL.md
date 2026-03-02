---
name: skills-manager
description: 在当前 `my-skills` 仓库中统一发现、导入、创建、更新、审计、优化、分发和发布 Skills 的总控 skill。Use when the user wants to: (1) 查找可用 skill, (2) 从 GitHub/URL/本地路径导入 skill, (3) 创建或 bootstrap 新 skill, (4) 更新已托管 skill, (5) 生成中文优化版 managed skill, (6) 分发到 Codex 或 Claude Code, (7) 提交并推送技能仓库变更。
---

# Skills Manager

使用这个 skill 作为当前仓库 `my-skills` 的统一技能控制面。

## Core Rules

1. 以当前仓库为唯一真源，所有托管 skill 都进入 `catalog/`。
2. 每个导入 skill 使用双轨结构：
   - `catalog/skills/<skill-id>/upstream/`
   - `catalog/skills/<skill-id>/managed/`
3. 只从 `managed/` 分发到 agent 目录。
4. `upstream/` 保持原始导入版本，正常流程下不要手工编辑。
5. 默认半自动模式：
   - 自动执行：发现、下载到临时目录、风险筛查、生成 managed、更新 registry、生成报告
   - 需要确认：覆盖已有 skill、分发到 agent、`git commit`、`git push`

## Task Routing

根据任务类型按需读取 reference：

- 查找或导入外部 skill：读 `references/find-and-import.md`
- 创建新 skill 或将本地目录纳管：读 `references/create-and-bootstrap.md`
- 更新已托管 skill：读 `references/update-and-refresh.md`
- 判断风险或审计结果：读 `references/audit-and-risk.md`
- 生成中文优化 managed：读 `references/refine-and-manage.md`
- 同步到 Codex / Claude Code：读 `references/distribute-to-agents.md`
- 提交或推送仓库：读 `references/git-publish.md`
- 查询目录和 JSON 结构：读 `references/catalog-schema.md`

先读 `references/overview.md` 了解全局约束，再进入具体模块。

## Scripts

优先使用内置脚本，避免重复编写仓库管理命令：

- `bash scripts/bootstrap_catalog.sh`
- `bash scripts/import_skill.sh`
- `bash scripts/update_skill.sh`
- `bash scripts/refresh_managed_state.sh`
- `bash scripts/sync_agents.sh`
- `bash scripts/publish_repo.sh`

这些脚本使用相对路径并在运行时解析仓库根目录。
