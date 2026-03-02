# Distribute To Agents

## Goal

把 `managed/` 中的 skill 分发到目标 agent 技能目录。

## Supported Targets In V1

- Codex
- Claude Code

## Source Of Truth

只从：

- `catalog/skills/<skill-id>/managed/`

进行分发。

## Deploy Order

1. 解析目标目录
2. 优先创建 symlink
3. 失败时 fallback 为 copy
4. 更新 `catalog/agents/<agent>.json`
5. 向用户报告实际部署方式

## Confirmation Boundary

分发前必须确认：

- 分发哪些 skill
- 分发到哪些 agent

## Target Directories

第一版目标：

- Codex: `~/.codex/skills`
- Claude Code: `~/.claude/skills`
