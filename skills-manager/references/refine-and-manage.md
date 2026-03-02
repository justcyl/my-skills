# Refine And Manage

## Goal

从 `upstream/` 生成中文优化版 `managed/`。

## Rules

1. `upstream/` 保持原样。
2. `managed/` 由大模型基于 upstream 直接生成。
3. 目标是中文化、结构优化、触发条件清晰化。
4. 尽量保留脚本、目录结构和关键资源。
5. 如果用户后续手动改动 `managed/`，应标记 `managed_dirty = true`。

## Optimization Targets

- frontmatter 中的 `description` 更容易触发
- 说明更短、更明确
- 工作流按步骤组织
- 长内容拆到 `references/`
- 重复代码或命令尽量指向 `scripts/`

## Report Output

生成 managed 后，在报告中写入：

- 是否已翻译为中文
- 主要结构改动
- 是否保留了原始脚本和资源
