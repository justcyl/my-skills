---
name: skill-creator
description: 兼容入口。该技能已并入 `skills-manager`，当用户要创建、重写、评测或优化 skill 时，优先改用 `skills-manager` 并路由到其内置的 `subskills/skill-creator/`。
---

# Skill Creator

这个顶层 skill 已降级为兼容入口。

实际流程入口在：

`/Users/chenyl/project/my-skills/skills-manager/subskills/skill-creator/SKILL.md`

如果当前任务与创建或评测 skill 有关，应交给 `skills-manager` 做场景路由，再进入上述子技能。
