---
name: skill-creator
description: 在 `my-skills` 仓库内创建、重写、评测并优化 skill 的子技能。只在 `skills-manager` 已把任务路由到创建场景时使用。负责需求访谈、SKILL.md 设计、测试集、benchmark、review viewer 和 description optimization；不负责仓库分发、归档或发布。
---

# Skill Creator

这是 `skills-manager/creator/` 下面的创建子技能，不是独立的总控。

## Scope

这个子技能负责：

1. 需求访谈与 skill 结构设计
2. 编写或重写根目录 skill 的 `SKILL.md`、`references/`、`scripts/`
3. 设计测试集并组织评测迭代
4. 优化 `description` 的触发效果

这个子技能不负责：

1. 搜索外部 skill
2. 导入、更新上游
3. 分发到 agent
4. 提交与推送

这些动作统一回到 `skills-manager` 执行。

## Working Root

1. 仓库根目录固定为 `MY_SKILLS_REPO_ROOT`，默认 `/Users/chenyl/project/my-skills`
2. 真正的 skill 内容固定在仓库根目录 `<skill-id>/`
3. 评测与中间产物固定放在 `.skills/workspaces/<skill-id>/`
4. 如果目标 skill 尚不存在，应先让 manager 运行 `bash scripts/create_skill.sh ...`

## Routing

不要一次加载全部 reference。按任务读取：

1. 用户要新建 skill、重写 skill 结构、把经验沉淀成 skill：
   读 `references/create-flow.md`
2. 用户要跑测试集、benchmark、viewer 审阅、盲评或迭代修订：
   读 `references/eval-flow.md`
3. 用户要优化 frontmatter 中的 `description` 触发效果：
   读 `references/description-flow.md`

## Shared Resources

按需使用这些资源：

1. `agents/grader.md`
2. `agents/analyzer.md`
3. `agents/comparator.md`
4. `references/schemas.md`
5. `eval-viewer/generate_review.py`
6. `scripts/*.py`

## Finish

子技能完成内容工作后，不要自己做发布；回到仓库根目录执行：

```bash
bash skills-manager/scripts/finalize_manual_edits.sh --skill-id <id> --publish --push
```
