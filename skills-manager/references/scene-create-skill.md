# Scene: Create Skill

当用户要“从零创建 skill / 重建 skill / 把现有做法沉淀为 skill / 迭代优化 skill”时读取本文件。

## Goals

1. 用统一骨架快速创建可纳管 skill
2. 吸收 `skill-creator` 的访谈、写作和验证流程
3. 保持脚本生成状态字段，LLM 负责内容质量
4. 创建后立即进入审计、分发、发布闭环

## Intake (先问清楚再创建)

至少确认这 5 项：

1. 这个 skill 要让 agent 完成什么能力
2. 触发条件和典型用户话术是什么
3. 输出格式或交付物是什么
4. 成功标准和失败边界是什么
5. 是否需要测试集与迭代评估

## Creation Command

```bash
bash scripts/create_skill.sh --skill-id <id> --name <name> --description <description>
```

脚本负责：

1. 创建根目录 `<skill-id>/`
2. 初始化 `SKILL.md`、`references/`、`scripts/`
3. 初始化 `.skills/sources/<id>.json`
4. 初始化 `.skills/reports/<id>.md`
5. 更新 `.skills/registry.json`

## Writing Rules (吸收 skill-creator 核心要求)

1. `description` 必须写触发条件，不只写功能名。
2. `SKILL.md` 主体聚焦工作流与边界，避免堆砌样例。
3. 大体量知识放 `references/`，可执行步骤放 `scripts/`。
4. 优先解释“为什么这样做”，减少僵硬指令。

## Two Tracks

### Track A: Fast Path (默认)

适用于大多数创建任务：

1. 创建骨架
2. 填充 `SKILL.md` 与必要 `references/`
3. 补最少可执行示例
4. finalize 收尾并发布

### Track B: Eval Path (按需)

当用户要求稳定性验证或准备长期复用时启用：

1. 设计 2-3 个真实测试 prompt
2. 跑一轮结果并收集反馈
3. 修订 `SKILL.md` 与辅助脚本
4. 重复直到可用

## Eval Toolkit (merged from skill-creator)

当进入 Track B 时，直接复用以下资源：

1. `toolkits/skill-creator/agents/grader.md`
2. `toolkits/skill-creator/agents/analyzer.md`
3. `toolkits/skill-creator/agents/comparator.md`
4. `toolkits/skill-creator/references/schemas.md`
5. `toolkits/skill-creator/eval-viewer/generate_review.py`
6. `toolkits/skill-creator/scripts/*.py`

典型命令（在 `skills-manager/toolkits/skill-creator/` 下执行）：

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
python -m scripts.run_loop --eval-set <path> --skill-path <path> --model <model> --max-iterations 5 --verbose
python -m scripts.package_skill <path/to/skill-folder>
```

## Source Of Truth

脚本生成（禁止 LLM 臆造）：

1. `skill_id`
2. `.skills/*.json` 状态字段
3. 哈希、时间戳、分发状态
4. 风险状态初值与更新

LLM 生成或修改：

1. `<skill-id>/SKILL.md` 正文
2. `<skill-id>/references/*.md`
3. `<skill-id>/scripts/*`
4. `.skills/reports/<skill-id>.md` 的可读说明段落

## Finish

任何创建或迭代后都执行：

```bash
bash scripts/finalize_manual_edits.sh --skill-id <id> --publish --push
```
