# Scene: Manage Skills

当用户要同步状态、处理手动编辑、分发、查询状态、归档或发布 skill 时读取本文件。

## Scope

这个场景负责：

1. 手动编辑后的状态刷新与审计
2. 分发到 Codex / Claude Code / Agents
3. 查看分发状态
4. 归档 skill
5. 在需要时提交并推送

## Git Workspace Hygiene

开始执行本场景前：

```bash
git -C ~/project/my-skills status --short
```

若输出非空，先执行：

```bash
git -C ~/project/my-skills add -A
git -C ~/project/my-skills commit -m "<message>"
```

结束本场景前重复上述检查。若仍有改动，必须再次使用上述 git 命令提交，直到工作区干净。

## Manual Edit Follow-up

单个 skill：

```bash
bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push
```

全部 skill：

```bash
bash skills-manager/scripts/sync_skill_state.sh --push
```

该脚本会：

1. 读取根目录 skill
2. 更新 `.skills/sources/*.json`
3. 更新 `.skills/registry.json`
4. 重写 `.skills/reports/*.md`
5. 重新做规则审计
6. 默认触发分发
7. 默认自动 `git add -A && git commit`；若传 `--push`，自动 `git push`
8. 若传 `--non-commit`，跳过提交与推送

## Distribution

同步分发：

```bash
bash skills-manager/scripts/distribute_skills.sh sync
```

常见参数：

1. `--agent codex|claude-code|agents|all`
2. `--skill-id <id>`
3. `--mode auto|symlink|copy`
4. `--dry-run`

归档也支持 `--dry-run`：

```bash
bash skills-manager/scripts/distribute_skills.sh archive --skill-id <id> [--dry-run]
```

查看状态：

```bash
bash skills-manager/scripts/distribute_skills.sh status
```

## Archive

归档某个 skill：

```bash
bash skills-manager/scripts/distribute_skills.sh archive --skill-id <id>
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
5. 场景开始前与结束后都必须保持 `git -C ~/project/my-skills status --short` 为空；不为空时由 agent 直接执行 git 命令提交（不得通过脚本代提）
