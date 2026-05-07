---
name: alan-pipeline
description: 管理研究项目的 card（知识单元）。当用户需要记录实验发现、提出假设、做出决策时使用。适用于 alan/ 目录存在的项目。
---

# Research Pipeline

用 card 作为原子单元驱动研究项目。

- **Card** — 一张说一件事的知识卡片，按类别存放，有结构性编号

```
alan/
  cards/
    method/<slug>.md       # 方法论 cards (p0, p1)
    exp/<slug>.md          # 实验与结果 cards (p0, p1)
    framing/<slug>.md      # 叙事框架 cards (p0, p1)
    archived/<slug>.md     # 归档 cards (p2，不分类别)
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
ls alan/cards/method/
ls alan/cards/exp/
grep -l "priority: p0" alan/cards/method/*.md
grep -rn "method/debiased-sorting#2" alan/cards/
```

## 规则

- **一事一卡**：一张 card 只说一件事。有重叠就拆分 + 引用。
- **不捏造**：数据、引用不编造。不确定就标 TBD。
- **不重复**：card 之间用路径引用，不复制内容。
- **不删除**：不要的 card 降为 p2 移入 archived/。
- **Active 不过时**：新建/修改 card 时检查关联 cards，过时就降级。

## Git 维护

每次修改 card（创建、编辑、归档）后，立即提交：

```bash
git add alan/cards/
git commit -m "pipeline: update cards (<列出变更的 slug>)"
```
