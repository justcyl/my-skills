# Scene: Distribute And Manage

当用户要管理分发、指定 agent、指定 skill、指定同步模式或查询状态时读取本文件。

## Default Rule

根目录 skill 是分发源。

## Sync

默认同步：

```bash
bash scripts/distribute_skills.sh sync
```

常见参数：

- `--agent codex|claude-code|all`
- `--skill-id <id>`
- `--mode auto|symlink|copy`
- `--dry-run`

## Status

查看分发状态：

```bash
bash scripts/distribute_skills.sh status
```

也可以限定 agent 或 skill：

```bash
bash scripts/distribute_skills.sh status --agent codex --skill-id <id>
```

## State Files

- `.skills/agents/codex.json`
- `.skills/agents/claude-code.json`
- `.skills/registry.json` 中的 `distribution`

## Policy

1. 默认优先 `symlink`
2. 失败时自动回退到 `copy`
3. 如果用户明确指定 `copy`，不要再尝试 `symlink`
