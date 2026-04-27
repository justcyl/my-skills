# Run Schema

Run 是行动单元，驱动项目推进。

## 目录结构

每个 run 独占一个文件夹：

```
alan/runs/<slug>/
  run.yaml        # Run 定义
  progress.md     # 执行历史
  notes           # 人工笔记（可选）
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

```markdown
# Progress

| Round | Verdict | Summary |
|-------|---------|---------|
| 1     | loop    | 做了 X，发现 Y |
| 2     | end     | 完成，产出 exp card |
```

每轮执行结束追加一行。ROUND 由行数派生，崩溃后重启自动接续。

## 执行协议

每轮循环：

1. 读取 `context`、`instruction`、`verifier`，注入 progress 历史和 notes
2. 执行（方式由 agent 自主决定）
3. 按 `verifier` 判断：`loop` → 追加 progress，进入下一轮；`end` → 追加 progress，写 `state: done`

## 一次性 vs 循环

格式完全相同，区别只在 verifier：

| | 一次性 | 循环 |
|---|---|---|
| verifier | 全完成 → end | 达标 → end，否则 → loop |

## 示例

### 一次性 Run

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
