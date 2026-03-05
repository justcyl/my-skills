# Scene: Distribute And Manage

当用户要管理分发、指定 agent、指定 skill、指定同步模式、查询状态或归档 skill 时读取本文件。

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

## Archive

归档某个 skill（从活跃技能中移除，并停止分发）：

```bash
bash scripts/distribute_skills.sh archive --skill-id <id>
```

预演：

```bash
bash scripts/distribute_skills.sh archive --skill-id <id> --dry-run
```

归档后：

1. skill 目录会移动到 `.skills/archived-skills/<id>/`
2. Codex / Claude Code 下对应 skill 会被移除
3. `.skills/registry.json` 与 `.skills/agents/*.json` 会同步更新

## State Files

- `.skills/agents/codex.json`
- `.skills/agents/claude-code.json`
- `.skills/registry.json` 中的 `distribution`

## Policy

1. 默认优先 `symlink`
2. 失败时自动回退到 `copy`
3. 如果用户明确指定 `copy`，不要再尝试 `symlink`
