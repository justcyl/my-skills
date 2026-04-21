# Run Schema

Run 是行动单元，驱动项目推进。三个字段定义一个 run，CLI 负责执行和循环。

## 文件位置

```
.pipeline/runs/<slug>.yaml          定义（不可变）
.pipeline/runs/<slug>.progress.md   执行历史（CLI 追加）
.pipeline/runs/<slug>.notes         用户笔记（agent 写，CLI 消费）
.pipeline/runs/<slug>.state         机器状态（CLI 管理）
```

## 字段定义

```yaml
context: |
  背景知识。引用 card 路径、实验条件、约束。
  提供 session 理解任务所需的一切信息。

instruction: |
  做什么。高层意图 + 具体步骤。
  每轮 session 按此执行。

verifier: |
  怎么判断。session 结束前按此评估。
  输出 verdict: end（完成）或 loop（继续下一轮）。
```

仅三个必填字段。可选字段：

| 字段 | 用途 | 示例 |
|------|------|------|
| `model` | 每轮 session 使用的模型 | `anthropic/claude-sonnet-4-20250514` |
| `thinking` | 思考等级 | `medium` |
| `tags` | 标签，方便查找 | `[autoresearch, lr]` |
| `prediction` | 实验前的预期结果，用于事后对比和 surprise 判断 | `"预计 acc 提升 ~1.5%"` |
| `experiment` | 实验快照配置 | 见 [experiment-run.md](experiment-run.md) |

## 一次性 Run vs 循环 Run

**区别只在 verifier 的内容。** 格式完全相同。

| | 一次性 Run | 循环 Run |
|---|---|---|
| verifier | "全完成 → end" | "达标 → end，否则 → loop" |
| 轮数 | 1 | N |
| progress.md | 1 行 | N 行 |

## CLI 执行

```bash
# 执行 run（自动循环直到 verifier 返回 end）
bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug>

# 指定模型
bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug> --model anthropic/claude-sonnet-4-20250514

# 查看状态
bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug> --status

# 添加笔记（下一轮注入）
bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug> --note "试试 warmup 200 步"

# 预览 prompt（不执行）
bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug> --dry-run
```

每轮执行流程：

```
CLI 读取 yaml → 填模板（context + instruction + progress + notes + verifier）
  → pi --print（全新 session）
  → 解析 verdict
  → 追加 progress.md
  → verdict == end → 结束
  → verdict == loop → 下一轮
```

## 结构化输出

每轮 session 必须在最后输出：

````
```result
verdict: loop | end
summary: <一句话描述本轮做了什么>
```
````

CLI 解析此块决定循环或结束。

## 示例

### 一次性 Run：跑实验

```yaml
context: |
  基础模型：Llama-3-8B（见 cards/method/llama3-config）
  数据集：SynthWiki-32k
  不调超参，使用论文默认配置。

instruction: |
  验证 debiased k=1 能否匹配 k=5 精度。
  跑 3 seeds (42/43/44) 对比 BLEU。
  每个 seed 完成后记录结果。
  全部完成后产出 exp card。

verifier: |
  检查：
  1. 3 seeds 都跑完了吗？
  2. BLEU mean±std 记录了吗？
  3. exp card 产出了吗？

  全部完成 → end
  否则 → loop，说明还缺什么
```

### 循环 Run：Autoresearch

```yaml
model: anthropic/claude-sonnet-4-20250514
thinking: medium

context: |
  研究问题：找到最优学习率调度策略。
  可改文件：train.py
  不可动文件：eval.py, prepare.py
  评测命令：python eval.py
  指标：accuracy，方向 maximize
  训练命令：python train.py（超时 300s）

instruction: |
  1. 分析最近几轮的实验历史和用户提示
  2. 设计一个改进策略，修改 train.py
  3. 合规检查：运行 git diff --name-only
     如果有非 train.py 的文件被改 → git checkout -- . → 报告 compliance_failed
  4. 训练：python train.py
  5. 评测：python eval.py，提取 accuracy
  6. 如果 accuracy 优于 progress 中记录的 best：
     → git add -A && git commit -m "R{round}: <策略描述>"
     否则 → git checkout -- .

verifier: |
  解析本轮 accuracy。
  检查 progress 历史中的最佳值。
  accuracy >= 0.95 或 round >= 50 → end
  否则 → loop
```

### 循环 Run：论文写作迭代

```yaml
context: |
  论文草稿在 drafts/paper.tex
  目标：ACL 2026 投稿

instruction: |
  阅读当前草稿，找出最需要改进的一个方面。
  做出具体修改。
  用 latex 编译验证无报错。

verifier: |
  检查 drafts/paper.tex 是否编译通过。
  检查是否有实质性内容改进（不是纯格式）。

  如果改进有价值 → loop（继续找下一个改进点）
  如果草稿已经足够好，没有明显可改之处 → end
```

## 监控

在 pi session 中，通过 herdr 启动监控子代理：

```
1. herdr pane_split direction=down newPane=run-monitor
2. herdr run pane=run-monitor command="bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug> --status"
```

或者直接读取状态文件：

```bash
read .pipeline/runs/<slug>.state
read .pipeline/runs/<slug>.progress.md
```

注入笔记：

```bash
bash -c 'echo "- 试试 warmup 200 步" >> .pipeline/runs/<slug>.notes'
```

## 崩溃恢复

所有状态在文件中。重新执行同一命令即从断点继续：

```bash
bash ~/.agents/skills/alan-pipeline/scripts/run.sh <slug>
# → 读 state 文件，从 round N+1 继续
```
