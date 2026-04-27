# Description Flow

当任务是"优化 SKILL.md frontmatter 中的 description 触发效果"时读取本文件。

当 skill 主体已经稳定后再做这一步——不要太早优化 description。

## Goal

让 `description` 更准确地触发 skill，同时减少误触发。

## Understanding Skill Triggering

skill 出现在模型的 `available_skills` 列表中，模型根据 name + description 决定是否咨询这个 skill。

重要：模型只会在无法轻松独立完成时才咨询 skill。简单查询即使 description 匹配也不会触发。复杂、多步骤或专业性强的查询才能可靠触发。因此 eval queries 应该足够有实质——模型必须确实能从 skill 中受益。

## Eval Set

1. 生成一组 should-trigger / should-not-trigger 查询（各 8-10 个）
2. 保存到 `.skills/workspaces/<skill-id>/description-evals.json`
3. 查询应尽量贴近真实用户输入，而不是抽象短句

### Eval Queries 的质量要求

查询必须像真实用户的输入——包含具体文件名、列名、公司名、个人上下文、URL、背景故事。混合长短句，聚焦边界 case。

**不要写**：`"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

**should-trigger 查询（8-10）**：同一意图的不同表达——正式和随意的、skill 没被显式命名但显然需要的、不常见用法、skill 与其他选项竞争但应该胜出的。

**should-not-trigger 查询（8-10）**：最有价值的是"近似命中"——共享关键词但实际需要不同东西的查询。相邻领域、歧义表达、另一个工具更合适的场景。不要写明显无关的查询。

## Review With User

读 `assets/eval_review.html` 模板，替换占位符：

- `__EVAL_DATA_PLACEHOLDER__` → JSON 数组
- `__SKILL_NAME_PLACEHOLDER__` → skill 名
- `__SKILL_DESCRIPTION_PLACEHOLDER__` → 当前 description

写入临时文件后 `open /tmp/eval_review_<skill-name>.html`。用户编辑后导出 `eval_set.json`。

这一步很重要——差的 eval queries 会导致差的 description。

## Run Optimization Loop

告知用户这需要一些时间：

```bash
python skills-manager/creator/scripts/run_loop.py \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

用驱动当前会话的模型 ID 来保持体验一致。

脚本流程：将 eval set 按 60%/40% 分为训练/测试集 → 评估当前 description（每个查询 3 次） → 用 Claude 基于失败 case 生成改进 → 在两个集上重新评估 → 迭代最多 5 次。按测试集得分选出 `best_description`（避免过拟合）。

定期 tail 输出给用户提供迭代进度和分数。

## Apply Result

1. 读取 `best_description`
2. 更新根目录 `<skill-id>/SKILL.md` frontmatter
3. 向用户展示前后对比和分数
4. 如果需要，再跑一轮 eval 确认结果
5. 完成后交回 manager finalize
