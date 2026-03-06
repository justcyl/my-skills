# Scene: Manage Skills

当用户要同步状态、处理手动编辑、分发、查询状态、归档或发布 skill 时读取本文件。

## Scope

这个场景负责：

1. 手动编辑后的状态刷新与审计
2. 分发到 Codex / Claude Code
3. 查看分发状态
4. 归档 skill
5. 在需要时提交并推送

## Manual Edit Follow-up

单个 skill：

```bash
bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push
```

全部 skill：

```bash
bash scripts/finalize_manual_edits.sh --publish --push
```

该脚本会：

1. 读取根目录 skill
2. 更新 `.skills/sources/*.json`
3. 更新 `.skills/registry.json`
4. 重写 `.skills/reports/*.md`
5. 重新做规则审计
6. 默认触发分发
7. 若传 `--publish`，自动 `git add -A && git commit`；若同时传 `--push`，自动 `git push`

## Distribution

同步分发：

```bash
bash scripts/distribute_skills.sh sync
```

常见参数：

1. `--agent codex|claude-code|all`
2. `--skill-id <id>`
3. `--mode auto|symlink|copy`
4. `--dry-run`

归档也支持 `--dry-run`：

```bash
bash scripts/distribute_skills.sh archive --skill-id <id> [--dry-run]
```

查看状态：

```bash
bash scripts/distribute_skills.sh status
```

## Archive

归档某个 skill：

```bash
bash scripts/distribute_skills.sh archive --skill-id <id>
```

归档后：

1. skill 会移动到 `.skills/archived-skills/<id>/`
2. agent 目录中的对应 skill 会被移除
3. `.skills/registry.json` 与 `.skills/agents/*.json` 会同步更新

## Policy

1. 根目录 skill 始终是唯一真源
2. 默认优先 `symlink`
3. 如果用户明确指定 `copy`，不要回退成 `symlink`
4. 如果审计结果为 `warned` 或 `blocked`，要人工复核是否继续分发
