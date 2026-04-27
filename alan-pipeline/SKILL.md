---
name: alan-pipeline
description: 管理研究项目的 card（知识单元）和 run（执行单元）。当用户需要记录实验发现、提出假设、做出决策、创建/执行研究任务时使用。Run 支持实验快照与结构化日志，确保 AI 训练实验可复现。适用于 alan/ 目录存在的项目。
---

# Research Pipeline

用 card 和 run 两种原子单元驱动研究项目。

- **Card** — 一张说一件事的知识卡片，按类别存放，有结构性编号
- **Run** — 一个可执行的行动单元（跑实验 / 写章节 / 验证假设）

```
alan/
  cards/
    method/<slug>.md       # 方法论 cards (p0, p1)
    exp/<slug>.md          # 实验与结果 cards (p0, p1)
    framing/<slug>.md      # 叙事框架 cards (p0, p1)
    archived/<slug>.md     # 归档 cards (p2，不分类别)
  runs/
    <slug>.yaml            # Run 定义（context + instruction + verifier）
    <slug>.progress.md     # 执行历史（CLI 自动追加）
    <slug>.notes           # 用户笔记（agent 写，CLI 消费）
    <slug>.state           # 机器状态（CLI 管理）
    <slug>.snapshot/       # 实验快照（含 experiment: 字段时建立）
```

## Card 操作

Card 是普通 Markdown 文件，用 `read`/`write`/`edit` 直接操作。

### 创建 card

```bash
write alan/cards/{category}/{slug}.md
```

文件结构：

```markdown
---
category: method           # method | exp | framing
priority: p0               # p0 | p1 | p2
tags: [keyword1, keyword2]
links:
  - cards/method/other-card
  - runs/some-run
---

# 标题

1-3 句摘要。

## 1. 第一个要点
...

## 2. 第二个要点
...
```

完整 schema 和示例见 [references/card-schema.md](references/card-schema.md)。

### Section 编号与跨卡片引用

每个 `##` section 必须有序号：`## 1.`、`## 2.`、…

**跨卡片引用**格式：`{category}/{slug}#{section}`

```
method/debiased-sorting#2    →  method/debiased-sorting.md 的 ## 2.
exp/bleu-baseline#1          →  exp/bleu-baseline.md 的 ## 1.
```

当用户说「改 method/debiased-sorting#2」，直接定位到对应文件的 `## 2.` section。

### Priority 分级

| 级别 | 含义 | 目录 |
|------|------|------|
| `p0` | 核心事实——已验证，长期有效，其他 card 依赖它 | `cards/{category}/` |
| `p1` | 中间状态——合理但脆弱，待验证或可能修改 | `cards/{category}/` |
| `p2` | 归档——被取代、被证伪、不再相关 | `cards/archived/` |

变更：p1→p0（多次验证后升级）、p1→p2 / p0→p2（移入 archived/，写明原因）。

### 归档（降为 p2）

```bash
mkdir -p alan/cards/archived
mv alan/cards/{category}/{slug}.md alan/cards/archived/{slug}.md
# edit frontmatter: priority: p2
# body 末尾加归档原因
```

归档后不保留原类别目录，统一放 `archived/`。

### 修改规则

**Slug 是身份。Slug 不变 = 同一张 card。**

| 操作 | 允许？ |
|------|--------|
| 改错别字、补格式 | ✅ |
| 补充/修改 section 内容 | ✅ |
| 新增 section（末尾追加新序号） | ✅ |
| 改变核心命题/主张 | ❌ 新建 card，旧 card 降为 p2 |
| 改变 category | ❌ 新建 card，mv 到对应目录 |

### 单一事实原则

**同一事实只存在于一张 card 中。** 创建新 card 前：

1. 检查现有 active cards 是否已覆盖相关内容
2. 如有重叠 → 提取重叠部分为独立小 card，原 card 改用引用：`见 method/debiased-sorting#1`
3. 不允许两张 card 说同一件事

### 维护

**p0 和 p1 cards 必须保持不过时。** 每当创建或修改 card 时：

1. 检查 links 中引用的 active cards 是否因新信息过时
2. 核心主张被取代 → 降为 p2，移入 archived/
3. 只需补充 → 原地修改（新增 section 或更新已有 section）

### 查找 card

```bash
ls alan/cards/method/                                # method cards
ls alan/cards/exp/                                   # exp cards
grep -l "priority: p0" alan/cards/method/*.md        # p0 method cards
grep -l "debiasing" alan/cards/**/*.md               # by tag
grep -rn "method/debiased-sorting#2" alan/cards/     # who references this section
```

## Run 操作

Run 是纯 YAML 文件，三个字段定义一切。通过 `write` 创建，通过 CLI 执行。

```yaml
# alan/runs/<slug>.yaml
state:        pending          # pending | done | archived（CLI 自动写 done；archived 由用户手动标记）
context:      背景知识（card 引用、实验条件、约束）
instruction:  做什么（高层意图 + 具体步骤）
verifier:     怎么判断（评估结果，输出 loop 或 end）
```

**一次性 run 和循环 run 格式完全相同。** 区别只在 verifier 是否返回 `loop`。

### 创建 run

```bash
write alan/runs/verify-debiased-k1.yaml
```

```yaml
state: pending
context: |
  基础模型：Llama-3-8B（见 cards/method/llama3-config）
  数据集：SynthWiki-32k
  不调超参，使用论文默认配置。

instruction: |
  验证 debiased k=1 能否匹配 k=5 精度。
  跑 3 seeds (42/43/44) 对比 BLEU。
  产出 exp card 记录结果。

verifier: |
  3 seeds 都跑完？BLEU 记录？exp card 产出？
  全部完成 → end
  否则 → loop
```

可选字段：`model`（完整模型字符串）、`thinking`（思考等级）、`tags`（标签）、`prediction`（实验前预测，用于事后对比 surprise）、`experiment`（实验快照）。

### 实验 Run

当 run 用于跑 AI 训练/评估实验时，在 YAML 中加 `experiment:` 字段。
执行前必须在 `alan/runs/<slug>.snapshot/` 中完成源码快照、环境文件保存、metadata 填写，
并在训练代码中配置结构化 JSONL 日志以确保指标可回放。

完整协议、目录结构、metadata 模板、日志接入、watch/replay 用法见
[references/experiment-run.md](references/experiment-run.md)。
实验设计哲学（如何构建对照、写预测、标记 surprise）也在同一文件开头。
日志组件 API 见 [references/logger-components.md](references/logger-components.md)。

### 执行 run

通过 CLI 执行。agent 创建 YAML 后，在 herdr 面板中启动：

```json
{"action": "pane_split", "direction": "down", "newPane": "run-exec"}
{"action": "run", "pane": "run-exec", "command": "bash ~/.agents/skills/alan-pipeline/scripts/run.sh verify-debiased-k1"}
```

或告知用户在另一个终端执行：

```bash
bash ~/.agents/skills/alan-pipeline/scripts/run.sh verify-debiased-k1
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--model <model>` | 覆盖模型（完整模型字符串）|
| `--thinking <level>` | 覆盖思考等级 |
| `--window N` | 每轮注入的 progress 历史行数（默认 5）|
| `--status` | 仅显示当前状态 |
| `--note "msg"` | 追加笔记供下一轮读取 |
| `--dry-run` | 预览 prompt，不执行 |

CLI 每轮创建全新 `pi --print` session（`--no-skills --no-context-files`，context 不积累），直到 verifier 返回 `end`。

### 查看状态

```bash
read alan/runs/<slug>.state       # 轮次、状态
read alan/runs/<slug>.progress.md  # 每轮记录
```

### 注入笔记（Human on the Loop）

```bash
bash -c 'echo "- 试试 warmup 200 步" >> alan/runs/<slug>.notes'
```

下一轮 session 会自动读到。

### Run 生命周期状态

`state` 字段存在于 run YAML 本身：

| 状态 | 含义 | 谁设置 |
|------|------|---------|
| `pending` | 待执行或执行中（默认）| 用户创建时 |
| `done` | verifier 返回 end | CLI 自动写入 |
| `archived` | 已退役，不再执行 | 用户手动设置 |

### 崩溃恢复

所有状态在文件中。重新执行同一命令从断点继续。

### 监控（可选）

在 pi 中通过 herdr 启动监控子代理：

**Step 1** — 分割面板
```json
{"action": "pane_split", "direction": "down", "newPane": "run-monitor"}
```

**Step 2** — 启动监控（周期检查 state 文件）
```json
{"action": "run", "pane": "run-monitor", "command": "watch -n 30 'cat alan/runs/<slug>.state && echo --- && tail -5 alan/runs/<slug>.progress.md'"}
```

**Step 3** — 读取输出
```json
{"action": "read", "pane": "run-monitor", "source": "visible"}
```

Run 完整字段定义和示例见 [references/run-schema.md](references/run-schema.md)。

## Card 与 Run 的关系

```
method card ──── 定义方法 ────→ run（验证实验，CLI 执行）
                                  │
                                  ▼ 产出（progress.md 记录）
                               exp card
                                  │
                                  ▼ 支撑
framing card ←── 引用 exp card 的结果构建叙事
      │
      ▼ 驱动
   下一个 run
```

Run 的 progress.md 是执行日志。如果某轮产出了对项目有持久意义的发现，应升级为 card。

## 规则

- **一事一卡**：一张 card 只说一件事。有重叠就拆分 + 引用。
- **不捏造**：数据、引用不编造。不确定就标 TBD。
- **不重复**：card 之间用路径引用（`见 method/debiased-sorting#2`），不复制内容。
- **不删除**：不要的 card 降为 p2 移入 archived/。
- **Progress 不沉淀知识**：任务级记录留 progress.md；项目级升级为 card。
- **Active 不过时**：新建/修改 card 时检查关联 cards，过时就降级。

## Git 维护

每次修改 card（创建、编辑、归档）后，立即提交：

```bash
git add alan/cards/
git commit -m "pipeline: update cards (<列出变更的 slug>)"
```

保持 `alan/cards/` 下没有未提交的变更。
