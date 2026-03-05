---
name: skills-manager
description: 统一处理所有 skills 操作的总控 skill，包括搜索、导入、创建、手动编辑后同步、规则与语义审核、中文优化、上游跟踪、分发、归档与发布。默认将所有下载/托管技能集中到 `my-skills` 仓库管理；即使在其他路径触发，也应回到该仓库执行管理流程。
---

# Skills Manager

使用这个 skill 作为统一技能仓库（`my-skills`）的唯一技能控制面。

## Repository Resolution

1. 默认目标仓库是 `/Users/chenyl/project/my-skills`。
2. 即使该 skill 在其他路径触发，也要把“下载、创建、更新、状态同步、分发、发布”统一落在这个仓库里。
3. 如需迁移仓库位置，可设置环境变量 `MY_SKILLS_REPO_ROOT` 覆盖默认路径。

## True Source

1. 仓库根目录下的每个 skill 目录就是唯一真源，例如 `find-skills/`、`skills-manager/`、`tm/`。
2. 不再维护第二份 `managed/` 副本。模型和用户都直接编辑根目录 skill。
3. 所有程序状态写入 `.skills/`：
   - `.skills/registry.json`
   - `.skills/sources/<skill-id>.json`
   - `.skills/reports/<skill-id>.md`
   - `.skills/agents/<agent>.json`
   - `.skills/upstream/<skill-id>/`
4. `skill_id`、哈希、状态字段、分发记录只能由脚本生成，不能由大模型臆造。
5. `SKILL.md`、`references/`、`scripts/` 这些技能内容可以由大模型生成或修改。
6. 归档技能统一移动到 `archived-skills/<skill-id>/`，不参与默认分发。

## Default Behavior

1. 任何导致 `my-skills` 仓库变化的操作，都要在结束前完成：
   - 状态同步
   - 规则审计
   - 必要的大模型审阅
   - 分发到 agent
   - 提交并推送仓库
2. 对外部 skill：
   - 可以使用 `npx skills find` 搜索
   - 不能使用 `npx skills add/check/update` 来管理本仓库
3. 对外部 skill 的审核分两层：
   - 脚本做规则审计与一致性检查
   - 大模型做语义审计，判断是否存在恶意 prompt、越权指令、模糊授权或危险工作流
4. 对外部 skill 的优化：
   - 先保存上游原始快照到 `.skills/upstream/<skill-id>/`
   - 再直接修改根目录 skill，使其成为中文优化版

## Routing

先判断用户属于哪一类场景，然后只读取对应 reference：

1. 用户要找 skill、下载 skill、更新外部 skill、查看上游信息：
   读 `references/scene-find-and-import.md`
2. 用户要创建新 skill 或重建 skill 骨架：
   读 `references/scene-create-skill.md`
3. 用户已经手动编辑了 skill，希望你补齐状态、审计、说明、同步、发布：
   读 `references/scene-manual-edit-followup.md`
4. 用户要管理某个 agent、某个 skill 的分发、同步模式、状态或归档：
   读 `references/scene-distribute-and-manage.md`
5. 当你需要确认 `.skills/` 内哪些字段由脚本生成、哪些内容由模型生成时：
   读 `references/schema-and-state.md`

不要先读所有 reference。只加载当前场景真正需要的那一个。

## Primary Scripts

优先使用下面 4 个场景脚本：

- `bash scripts/find_or_import_skill.sh ...`
- `bash scripts/create_skill.sh ...`
- `bash scripts/finalize_manual_edits.sh ...`
- `bash scripts/distribute_skills.sh ...`

仓库发布由辅助脚本处理：

- `bash scripts/publish_repo.sh ...`

## Workflow

### 1. Find And Download Skills

当用户要找现成 skill 或导入外部 skill：

1. 先理解需求与目标场景。
2. 如果来源不明确，可先用 `npx skills find` 搜索。
3. 选定来源后，用 `bash scripts/find_or_import_skill.sh import ...` 导入到仓库根目录。
4. 脚本完成后，人工查看规则审计结果；必要时做语义审计。
5. 直接在根目录 skill 上完成中文优化与说明书整理。
6. 运行 `bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push`。

### 2. Create Skills

当用户要新建 skill：

1. 先明确 skill 触发条件、边界和资源结构。
2. 用 `bash scripts/create_skill.sh ...` 创建骨架。
3. 在根目录 skill 中填充 `SKILL.md`、`references/`、`scripts/`。
4. 运行 `bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push`。

### 3. Manual Edit Follow-up

当用户已经改了某个 skill：

1. 不要再创建副本或复制到别处。
2. 直接对修改后的根目录 skill 做状态刷新与审计。
3. 运行 `bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push`。

### 4. Distribution And Management

1. 默认分发源是仓库根目录 skill。
2. 一般情况下，状态同步完成后应自动分发。
3. 当用户需要指定 agent、指定 skill、指定 `symlink/copy` 时，使用 `bash scripts/distribute_skills.sh ...`。
4. 当用户要求归档某个 skill 时，使用 `bash scripts/distribute_skills.sh archive --skill-id <id>`。

## Output Rules

每次完成场景处理后，给用户一个简短结果：

- 做了什么
- 哪个 skill 受影响
- 审计状态
- 是否已分发
- 是否已提交 / 推送
