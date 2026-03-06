# Description Flow

当任务是“优化 SKILL.md frontmatter 中的 description”时读取本文件。

## Goal

让 `description` 更准确地触发 skill，同时减少误触发。

## Eval Set

1. 生成一组 should-trigger / should-not-trigger 查询
2. 保存到 `.skills/workspaces/<skill-id>/description-evals.json`
3. 查询应尽量贴近真实用户输入，而不是抽象短句

## Review

需要人工审查时，可使用：

`skills-manager/subskills/skill-creator/assets/eval_review.html`

## Optimization Command

从仓库根目录直接调用：

```bash
python skills-manager/subskills/skill-creator/scripts/run_loop.py --eval-set /Users/chenyl/project/my-skills/.skills/workspaces/<skill-id>/description-evals.json --skill-path /Users/chenyl/project/my-skills/<skill-id> --model <model> --max-iterations 5 --verbose
```

## Apply

1. 读取 `best_description`
2. 更新根目录 `<skill-id>/SKILL.md` frontmatter
3. 如果需要，再跑一轮 eval 确认结果
4. 完成后交回 manager finalize
