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
2. 技能内容直接在根目录 skill 目录中维护，作为唯一工作副本。
3. 所有程序状态写入 `.skills/`：
   - `.skills/registry.json`
   - `.skills/sources/<skill-id>.json`
   - `.skills/reports/<skill-id>.md`
   - `.skills/agents/<agent>.json`
   - `.skills/upstream/<skill-id>/`
   - `.skills/workspaces/<skill-id>/`
4. `skill_id`、哈希、状态字段、分发记录只能由脚本生成，不能由大模型臆造。
5. `SKILL.md`、`references/`、`scripts/` 这些技能内容可以由大模型生成或修改。
6. 归档技能统一移动到 `.skills/archived-skills/<skill-id>/`，不参与默认分发。

## State Schema (Always Loaded)

为了避免需要额外加载子文件才能理解状态约束，这里直接定义状态结构：

- 状态目录：
  - `.skills/registry.json`
  - `.skills/sources/<skill-id>.json`
  - `.skills/reports/<skill-id>.md`
  - `.skills/agents/<agent>.json`
  - `.skills/upstream/<skill-id>/`
  - `.skills/workspaces/<skill-id>/`
  - `.skills/archived-skills/<skill-id>/`
- 只能由脚本生成的字段：
  - `skill_id`：技能唯一标识（目录和状态索引主键）。
  - `source_type`：来源类型（如 `github`、`local-bootstrap`、`local-created`）。
  - `source`：用户原始输入的来源值（repo 简写、URL 或路径）。
  - `source_url`：归一化后的可拉取地址（通常是 git URL）。
  - `ref`：上游分支或引用（如 `main`）。
  - `subpath`：来源仓库内 skill 所在子目录。
  - `bootstrap`：是否由本地初始化纳管得到。
  - `upstream_enabled`：是否启用上游跟踪和更新。
  - `risk_status`：规则审计结果（`passed` / `warned` / `blocked`）。
  - `upstream_revision`：上游版本标识（优先 commit SHA）。
  - `managed_revision`：当前根目录 skill 内容哈希。
  - `managed_dirty`：根目录 skill 是否存在未收尾变更。
  - `archived`：是否已归档。
  - `archived_at`：归档时间（UTC ISO8601）。
  - `last_imported_at`：最近一次导入或状态刷新时间。
  - `last_updated_at`：registry 条目最近更新时间。
  - `distribution`：各 agent 分发状态映射（路径、模式、同步状态、时间）。
  - agent state JSON：每个 agent 已分发技能的明细状态。
- 可由大模型生成或修改的内容：
  - 根目录 skill 的 `SKILL.md`
  - 根目录 skill 的 `references/*.md`
  - 根目录 skill 的 `scripts/*`
  - `.skills/reports/*.md` 中的人类可读解释与说明
- 边界：
  - 根目录 skill 是真实内容
  - `.skills/*.json` 是程序状态，不作为自由编辑文档
  - `.skills/upstream/` 存外部 skill 原始快照
  - `.skills/workspaces/` 存创建与评测过程的中间产物

## Default Behavior

1. 任何导致 `my-skills` 仓库变化的操作，都要在结束前完成：
   - 状态同步
   - 规则审计
   - 必要的大模型审阅
   - 分发到 agent
   - 提交并推送仓库
2. 对外部 skill：
   - 搜索统一使用 `bash scripts/find_or_import_skill.sh search <query>`
   - 禁止使用外部 Skills CLI 直接安装、检查或更新本仓库
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
   该模块已吸收原 `find-skills` 的触发话术、搜索呈现与导入决策流程。
2. 用户要创建新 skill 或重建 skill 骨架：
   读 `references/scene-create-skill.md`
   该模块只负责创建场景路由与状态入口。
   具体创建、评测、description 优化交给 `creator/SKILL.md`。
3. 用户要同步状态、处理手动编辑、分发、查询状态、归档或发布：
   读 `references/scene-manage-skills.md`

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
2. 如果来源不明确，先用 `bash scripts/find_or_import_skill.sh search <query>` 搜索。
3. 选定来源后，用 `bash scripts/find_or_import_skill.sh import ...` 导入到仓库根目录。
4. 脚本完成后，人工查看规则审计结果；必要时做语义审计。
5. 直接在根目录 skill 上完成中文优化与说明书整理。
6. 运行 `bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push`。

### 2. Create Skills

当用户要新建 skill：

1. 先用 `references/scene-create-skill.md` 判断是“新建 / 重写 / 评测 / description 优化”。
2. 如果目标 skill 尚不存在，先用 `bash scripts/create_skill.sh ...` 创建骨架与 `.skills/workspaces/<id>/`。
3. 把具体内容生产与评测工作路由给 `creator/SKILL.md`。
4. 子技能完成后，回到 manager 执行 `bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push`。

### 3. Manage Skills

当用户要处理已存在的 skill：

1. 继续以根目录 skill 目录作为唯一工作副本。
2. 手动编辑后的状态刷新与审计，使用 `bash scripts/finalize_manual_edits.sh ...`。
3. 分发、状态查询、归档使用 `bash scripts/distribute_skills.sh ...`。
4. 默认分发源是仓库根目录 skill。

## Output Rules

每次完成场景处理后，给用户一个简短结果：

- 做了什么
- 哪个 skill 受影响
- 审计状态
- 是否已分发
- 是否已提交 / 推送
