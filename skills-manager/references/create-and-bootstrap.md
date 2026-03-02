# Create And Bootstrap

## Use This Module

当用户要求以下任务时读取本模块：

- 创建一个新 skill
- 将当前目录或已有目录 bootstrap 成托管 skill
- 改造已有 skill 以纳入当前仓库管理

## Rules

1. 新建 skill 时，目录名优先作为稳定 `skill_id`。
2. 新建 skill 直接落入 `catalog/skills/<skill-id>/managed/`。
3. 如果没有明确外部来源，则 `source_type = local-bootstrap`。
4. 创建或 bootstrap 完成后，更新：
   - `catalog/sources/<skill-id>.json`
   - `catalog/reports/<skill-id>.md`
   - `catalog/locks/registry.json`

## Recommended Contents

优先保持 skill 简洁：

- `SKILL.md`
- 需要时再加 `references/`
- 需要确定性行为时再加 `scripts/`
- 需要 UI 元数据时加 `agents/openai.yaml`

避免生成额外说明性文档。
