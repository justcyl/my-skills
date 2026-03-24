# Scene: Create Skill

当用户要“新建 skill / 重写 skill / 评测 skill / 优化 skill description”时读取本文件。

## Role Split

`skills-manager` 只负责：

1. 识别当前是新建、重写、评测还是 description 优化
2. 确保所有操作都落在 `MY_SKILLS_REPO_ROOT` 指向的 `my-skills` 仓库
3. 在需要时先创建根目录 skill 骨架与 `.skills/workspaces/<skill-id>/`
4. 在子技能完成内容工作后执行 finalize、分发、提交、推送

具体的创建、评测和 description 优化，统一交给：

`creator/SKILL.md`

## Routing

1. 目标 skill 还不存在：
   先运行 `bash skills-manager/scripts/create_skill.sh --skill-id <id> --name <name> --description <description> [--force] [--dry-run]`，
   然后进入 `creator/SKILL.md`
2. 目标 skill 已存在，但用户要重写结构或扩展内容：
   直接进入 `creator/SKILL.md`
3. 用户只要评测、benchmark、viewer 审阅或 description 优化：
   直接进入 `creator/SKILL.md`
4. 用户只改了文件，希望同步状态并发布：
   不进入 creator，改读 `scene-manage-skills.md`

## Outputs Owned By Manager

脚本生成并维护：

1. 根目录 `<skill-id>/` 是否存在
2. `.skills/sources/<skill-id>.json`
3. `.skills/reports/<skill-id>.md`
4. `.skills/registry.json`
5. `.skills/workspaces/<skill-id>/`

## Handoff Back

子技能完成后，统一回到 manager 收尾：

```bash
bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push
```
