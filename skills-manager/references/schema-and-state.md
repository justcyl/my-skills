# Schema And State

本文件只说明 `.skills/` 中的状态结构与职责边界。

## State Directory

- `.skills/registry.json`
- `.skills/sources/<skill-id>.json`
- `.skills/reports/<skill-id>.md`
- `.skills/agents/<agent>.json`
- `.skills/upstream/<skill-id>/`
- `archived-skills/<skill-id>/`

## Script-Generated Fields

下面这些必须由脚本生成：

- `skill_id`
- `source_type`
- `source`
- `source_url`
- `ref`
- `subpath`
- `bootstrap`
- `upstream_enabled`
- `upstream_revision`
- `managed_revision`
- `managed_dirty`
- `archived`
- `archived_at`
- `last_imported_at`
- `last_updated_at`
- `distribution`
- agent state JSON

## LLM-Generated Content

下面这些是大模型可以生成或修改的内容：

- 根目录 skill 的 `SKILL.md`
- 根目录 skill 的 `references/*.md`
- 根目录 skill 的 `scripts/*`
- `.skills/reports/*.md` 中的人类可读解释与说明

## Root Skill vs State

- 根目录 skill：真实内容
- `.skills/*.json`：程序状态
- `.skills/upstream/`：外部 skill 的原始快照

不要把 `.skills/*.json` 当作自由编辑文档；它们是脚本状态文件。
