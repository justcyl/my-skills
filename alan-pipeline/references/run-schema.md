# Run Schema

Run 是行动单元，驱动项目推进。

## 目录结构

每个 run 独占一个文件夹：

```
alan/runs/<slug>/
  run.yaml        # Run 定义
  progress.md     # 执行历史（表格 + 自由内容）
  ...             # 执行过程产生的其他产物（日志、snapshot 等）
```

## run.yaml 字段

```yaml
state: pending             # pending（默认）| done | archived

context: |
  背景知识。引用 card 路径、实验条件、约束。

instruction: |
  做什么。高层意图 + 具体步骤。每轮执行。

verifier: |
  怎么判断完成。输出 verdict: end 或 loop。
```

`state` 生命周期：

| 值 | 含义 |
|----|------|
| `pending` | 待执行或执行中（默认，可省略） |
| `done` | 已完成（verifier 返回 end 时写入） |
| `archived` | 已退役，不再执行 |

可选字段：

| 字段 | 用途 |
|------|------|
| `model` | 指定模型（完整字符串，如 `anthropic/claude-opus-4`）|
| `thinking` | 思考等级 |
| `tags` | 标签 |
| `prediction` | 实验前预测，用于事后对比 surprise |
| `experiment` | 实验快照配置，见 [experiment-run.md](experiment-run.md) |

## progress.md 格式

progress.md 由两部分组成：**表格**（结构化摘要）和**自由 section**（详细内容）。

### 表格

```markdown
# Progress

| Round | Verdict | Summary | Insight | Note |
|-------|---------|---------|---------|------|
| 1     | loop    | 降 lr 到 3e-4，loss 下降 | lr 对收敛影响显著 | |
| 2     | loop    | 加 warmup 200 步 | warmup 无明显效果 | 用户：试试 cosine decay |
| 3     | end     | cosine 有效，acc 0.82 | cosine 比 step decay 稳定 | |
```

| 列 | 谁写 | 内容 |
|----|------|------|
| Round | agent | 轮次编号 |
| Verdict | agent | `loop` 或 `end` |
| Summary | agent | 本轮做了什么 |
| Insight | agent | 为什么有效/无效，学到了什么 |
| Note | 用户 | 下一轮的 hint（轮间填写，留空正常）|

ROUND 由数据行数派生，崩溃后重启自动接续。
Note 列：想在下一轮注入 hint，直接编辑当前最后一行的 Note 列，下一轮执行时自然读入上下文。

### 自由 section

表格只记摘要。对于信息量较大的任务，agent 可以在表格之后追加自由内容：

```markdown
## Round 1

详细发现、中间步骤、关键决策...

## Summary

run 完成后的整体总结、关键结论、后续建议。
```

**何时使用自由 section**：
- 单轮任务：一行表格装不下完整信息时，追加 `## Round 1` 详细记录
- 多轮任务：完成时写 `## Summary` 沉淀关键发现（比表格每行更完整）
- 任何轮次：有需要保留的中间推理、对比数据、决策过程时

> 持久性知识（对整个项目有意义的发现）应升级为 exp card，不要只存在 progress.md 里。

## 执行协议

每轮循环：

1. 读取 `context`、`instruction`、`verifier`，注入完整 progress 历史（含 Note 列）
2. 执行（方式由 agent 自主决定）
3. 追加 progress 表格新行（Note 列留空）
4. 按 `verifier` 判断：`loop` → 进入下一轮；`end` → 写 `state: done`，可追加 `## Summary`

## 多轮 Run 的子 Agent 模式

> 仅供参考，适用于**轮次多、单轮耗时长**的 run（如 autoresearch）。普通短程任务直接在当前 session 执行即可。

**适用条件**：预计轮次多（> 10 轮）或单轮执行时间长，主 session 在循环期间 context 会爆炸。

**执行方式**：通过 herdr 起一个独立 pi session（参考 pi-subagent skill），**不使用 `--print`**——子 agent 在自己的 session 里完整跑完所有轮次。

```json
{"action": "pane_split", "direction": "down", "newPane": "run-agent"}
{"action": "run", "pane": "run-agent", "command": "pi --skill ~/.agents/skills/alan-pipeline/SKILL.md --no-context-files --no-session 'Execute run: alan/runs/<slug>/run.yaml'"}
{"action": "wait_agent", "pane": "run-agent", "statuses": ["idle", "done"], "timeout": 7200000}
```

主 agent watch 直到子 agent idle（即子 agent 跑完所有轮、写好 `state: done`、结束对话）。
之后主 agent 读 `progress.md` 确认结果，决定后续动作。

**恢复点**：子 agent 崩溃时，`progress.md` 行数即已完成轮次，重新起一个子 agent 从下一轮接续。

## 一次性 vs 循环

格式完全相同，区别只在 verifier：

| | 一次性 | 循环 |
|---|---|---|
| verifier | 全完成 → end | 达标 → end，否则 → loop |

## 示例

### 一次性 Run（短程）

```yaml
state: pending

context: |
  基础模型：Llama-3-8B（见 cards/method/llama3-config）
  数据集：SynthWiki-32k

instruction: |
  验证 debiased k=1 能否匹配 k=5 精度。
  跑 3 seeds (42/43/44) 对比 BLEU。
  产出 exp card 记录结果。

verifier: |
  3 seeds 跑完？BLEU 记录？exp card 产出？
  全部完成 → end，否则 → loop
```

完成后 progress.md 可能长这样：

```markdown
# Progress

| Round | Verdict | Summary | Insight | Note |
|-------|---------|---------|---------|------|
| 1     | end     | 3 seeds 跑完，k=1 vs k=5 差距 0.3±0.1 | 差距在预测范围内 | |

## Summary

k=1 与 k=5 BLEU 差距 0.3±0.1（mean ± std），符合预测 < 0.5 的范围。
已产出 exp card: exp/debiased-k1-bleu。
结论：debiased k=1 可替代 k=5，推理成本降低 5x。
```

### 循环 Run：Autoresearch

```yaml
state: pending
model: anthropic/claude-opus-4

context: |
  目标：找到最优学习率调度策略。
  可改文件：train.py；不可动：eval.py, prepare.py
  评测命令：python eval.py；指标：accuracy（maximize）

instruction: |
  分析历史，设计改进策略，修改 train.py，训练并评测。
  accuracy 提升则 commit，否则 git checkout -- .

verifier: |
  accuracy >= 0.95 或 round >= 50 → end，否则 → loop
```
