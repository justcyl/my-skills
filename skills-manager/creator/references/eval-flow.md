# Eval Flow

当任务是“验证、迭代、benchmark、viewer 审阅或盲评”时读取本文件。

## Workspace

统一使用：

`/Users/chenyl/project/my-skills/.skills/workspaces/<skill-id>/`

推荐结构：

1. `.skills/workspaces/<skill-id>/evals/evals.json`
2. `.skills/workspaces/<skill-id>/iteration-1/`
3. `.skills/workspaces/<skill-id>/iteration-2/`
4. `.skills/workspaces/<skill-id>/skill-snapshot/`
5. `.skills/workspaces/<skill-id>/logs/`

## Default Eval Loop

1. 设计 2-3 个真实测试 prompt
   如果被测 skill 是路由型（包含多条路由分支），测试集必须覆盖每条路由分支，并包含至少一个跨分支的歧义 case
2. 在 workspace 下写 `evals/evals.json`
3. 对每个 case 跑 with-skill 与 baseline
4. 补 assertions 与 grading
5. 聚合 benchmark
6. 用 viewer 给用户审阅
7. 根据反馈修改根目录 `<skill-id>/`
8. 每轮迭代改完后，回到 manager 执行 `bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push` 完成提交推送
9. 继续下一轮，直到满意为止

## Tools

从仓库根目录直接调用：

```bash
python skills-manager/creator/scripts/aggregate_benchmark.py <workspace>/iteration-N
python skills-manager/creator/eval-viewer/generate_review.py <workspace>/iteration-N --skill-name <name>
```

如果需要正式 grading、分析或盲评，按需读取：

1. `agents/grader.md`
2. `agents/analyzer.md`
3. `agents/comparator.md`

## Notes

1. 根目录 `<skill-id>/` 是唯一真源
2. workspace 只存评测过程与中间结果
3. 每轮修改结束后，执行 `bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push` 提交推送
