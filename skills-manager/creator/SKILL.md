---
name: creator
description: 在 `my-skills` 仓库内创建、重写、评测并优化 skill。只在 `skills-manager` 已把任务路由到创建场景时使用。负责需求访谈、SKILL.md 设计、测试集、benchmark、review viewer、description optimization 和打包；不负责仓库分发、归档或发布。
---

# Skill Creator

## Scope

负责：需求访谈与 skill 设计、编写或重写根目录 skill 的内容、设计测试集与组织评测迭代、优化 description 触发效果、打包 `.skill` 文件。

不负责：搜索、导入、上游更新、分发、归档、提交推送——这些统一交回 `skills-manager`。

## Working Root

仓库根目录固定为 `MY_SKILLS_REPO_ROOT`（默认 `~/project/my-skills`）。

- 真实 skill 内容：`<skill-id>/`
- 评测与中间产物：`.skills/workspaces/<skill-id>/`
- 打包产物：`.skills/packages/`

如果目标 skill 尚不存在，先让 manager 运行 `bash skills-manager/scripts/create_skill.sh ...`。

> 注意：creator 内脚本路径前缀为 `skills-manager/creator/scripts/...`，manager 脚本前缀为 `skills-manager/scripts/...`。

## Routing

按任务类型读取对应 reference，不要同时加载多个：

1. **新建 / 重写 skill，从对话轨迹沉淀 skill**：读 `references/create-flow.md`
2. **测试 / 评测 / benchmark / viewer 审阅 / 迭代改进**：读 `references/eval-flow.md`
3. **优化 frontmatter 中的 description 触发效果**：读 `references/description-flow.md`

## How To Communicate

默认可直接使用：`evaluation`、`benchmark`、`workspace`。视用户熟悉度决定是否解释：`JSON`、`assertion`、`baseline`。目标是把 skill 做出来，不是展示术语。

## Shared Resources

按需读取：

**Agents:**
- `agents/grader.md` — 断言评分
- `agents/analyzer.md` — benchmark 分析与盲评后因分析
- `agents/comparator.md` — 两组输出盲评比较

**Scripts（从仓库根目录调用）:**
- `skills-manager/creator/scripts/run_eval.py` — 对指定 description 跑触发评测
- `skills-manager/creator/scripts/improve_description.py` — 基于评测结果生成改进 description
- `skills-manager/creator/scripts/run_loop.py` — eval + improve 迭代循环
- `skills-manager/creator/scripts/aggregate_benchmark.py` — 聚合多轮评测为 benchmark 统计
- `skills-manager/creator/scripts/generate_report.py` — 迭代循环结果生成 HTML 报告
- `skills-manager/creator/scripts/package_skill.py` — 打包为 `.skill` 文件
- `skills-manager/creator/scripts/quick_validate.py` — skill 基础结构快速校验

**Other:**
- `eval-viewer/generate_review.py` — 评测结果交互式审阅页面
- `assets/eval_review.html` — description 优化评审静态模板
- `references/schemas.md` — 所有 JSON 数据结构定义

## Finish

子技能完成内容工作后，统一回到 manager 收尾：

```bash
bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push
```
