# Scene: Create Skill

当用户要创建新 skill、重建 skill 骨架，或把一个想法转成正式 skill 时读取本文件。

## Goals

1. 创建根目录 skill 作为真源
2. 用最小骨架启动 skill
3. 明确哪些部分由脚本生成，哪些部分由大模型写内容
4. 创建后立即纳入 `.skills/` 状态管理

## Creation Workflow

先运行骨架脚本：

```bash
bash scripts/create_skill.sh --skill-id <id> --name <name> --description <description>
```

脚本负责：

- 创建根目录 skill
- 写入最小 `SKILL.md`
- 初始化 `references/`、`scripts/`
- 创建 `.skills/sources/<id>.json`
- 创建 `.skills/reports/<id>.md`
- 更新 `.skills/registry.json`

## Content Responsibilities

脚本生成：

- `skill_id`
- `.skills/*.json`
- 审计状态初值
- 哈希与时间戳

大模型生成：

- `SKILL.md` 正文
- `references/*.md`
- 需要时的 `scripts/*`
- 报告中的原理与用法说明

## Finish

内容补齐后，必须运行：

```bash
bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push
```
