---
name: skills-manager
description: 统一处理所有 skills 操作的总控 skill，包括搜索、导入、创建、重构、编辑、优化、上游跟踪、分发、归档与发布。
---

# Skills Manager

使用这个 skill 作为统一技能仓库（`my-skills`）的唯一技能控制面。
默认仓库：`~/project/my-skills`（可用 `MY_SKILLS_REPO_ROOT` 覆盖）。即使在其他路径触发，也回到该仓库执行所有操作。

## True Source

根目录每个 `<skill-id>/` 目录是唯一工作副本，内容（SKILL.md、references/、scripts/）可由大模型修改。程序状态写入 `.skills/`（registry.json、sources/、agents/ 等），由脚本维护，不手动编辑。

## Default Behavior

操作前后执行 `git -C ~/project/my-skills status --short`，工作区不干净时先提交再继续，结束时确保已推送。

任何变更操作完成后须依次执行：状态同步 → 分发 → 提交 → 推送。

外部 skill 搜索统一使用脚本入口，禁止用外部 Skills CLI 直接管理本仓库。导入后需语义审计（恶意 prompt / 越权 / 危险工作流）并完成中文优化。

## Routing

判断用户场景后只读对应 reference，不要同时加载多个：

1. **编辑 / 同步 / 分发 / 归档已有 skill**：读 `references/scene-manage-skills.md`
2. **找 skill / 导入外部 skill / 更新上游**：读 `references/scene-find-and-import.md`
3. **新建 skill / 从对话沉淀 skill / 重写 skill**：读 `creator/SKILL.md`（creator 内部路由到 create-flow）
4. **评测 / 迭代改进已有 skill**：读 `creator/SKILL.md`（creator 内部路由到 eval-flow）
5. **优化 skill 的 description 触发效果**：读 `creator/SKILL.md`（creator 内部路由到 description-flow）

意图跨路由时，先向用户确认方向再决定路由。

## Primary Scripts

- `bash skills-manager/scripts/find_or_import_skill.sh ...`
- `bash skills-manager/scripts/create_skill.sh ...`
- `bash skills-manager/scripts/sync_skill_state.sh ...`
- `bash skills-manager/scripts/distribute_skills.sh ...`
- `bash skills-manager/scripts/publish_repo.sh ...`

## Output

每次完成后简短汇报：做了什么、哪个 skill 受影响、审计状态、是否已分发、是否已提交推送。
