# Create Flow

当任务是“新建或重写 skill”时读取本文件。

## Inputs

至少确认这 5 项：

1. 这个 skill 要解决什么任务
2. 用户会怎么触发它
3. 输出或交付物是什么
4. 成功标准和失败边界是什么
5. 是否需要后续评测

## Files You Own

直接编辑仓库根目录 `<skill-id>/`：

1. `<skill-id>/SKILL.md`
2. `<skill-id>/references/*.md`
3. `<skill-id>/scripts/*`

不要把真实内容写到 `.skills/`。

## Writing Rules

1. `description` 既写功能，也写触发语境
2. `SKILL.md` 主体写流程、边界、输出格式
3. 大块资料放 `references/`
4. 稳定重复动作优先沉淀为 `scripts/`
5. 尽量解释“为什么”，少写僵硬口号

## Default Flow

1. 先确认 manager 已创建好骨架
2. 写出最小可用的 `SKILL.md`
3. 按需要补 `references/` 与 `scripts/`
4. 如果用户只要快速落地，到这里即可交回 manager finalize
5. 如果用户要求验证或长期维护，再进入 `eval-flow.md`
