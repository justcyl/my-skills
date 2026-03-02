# Scene: Manual Edit Follow-up

当用户已经手动编辑了 skill，希望你补齐状态、审计、分发和发布时读取本文件。

## Goals

1. 以根目录 skill 为唯一事实来源
2. 刷新程序状态，避免 `.skills/` 与真实文件不一致
3. 重新跑规则审计
4. 自动分发并发布

## Workflow

运行：

```bash
bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push
```

如果要处理全部 skill：

```bash
bash scripts/finalize_manual_edits.sh --publish --push
```

## What The Script Does

1. 读取根目录 skill
2. 重新计算哈希与时间戳
3. 更新 `.skills/sources/*.json`
4. 更新 `.skills/registry.json`
5. 重写 `.skills/reports/*.md`
6. 重新做规则审计
7. 默认触发分发
8. 根据参数决定是否提交和推送

## LLM Follow-up

脚本结束后，如果审计结果为 `warned` 或 `blocked`，必须人工判断：

- 风险是否可接受
- 是否需要重写指令
- 是否需要阻止分发
