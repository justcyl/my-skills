---
name: ph-paper-research
description: 使用 paper-helper (ph) CLI 进行学术论文检索与渐进式阅读。当 agent 需要查找论文、了解某研究领域的现状、获取论文摘要或精读全文时使用。覆盖完整工作流：初始化 workspace → 搜索 → L1 摘要筛选 → 按需获取 L2 全文。适用场景包括"帮我找关于 X 的论文"、"调研 Y 方向的工作"、"精读这篇论文"、"搜索 Z 作者的研究"。
---

# ph-paper-research

使用 `ph`（paper-helper）CLI 进行学术论文检索与渐进式阅读的完整操作指南。

## 核心概念：渐进式披露

`ph` 将论文信息分为两层：

- **L1（摘要级）**：通过 `ph paper search` 获取，包含标题、作者、摘要、发表信息。消耗少，适合快速筛选。
- **L2（全文级）**：通过 `ph paper fetch-fulltext` 获取，包含完整论文内容。需要 `MINERU_API_KEY`，消耗更多资源。

**原则**：先用 L1 筛选出真正需要深读的论文，再对少数论文获取 L2 全文。不要对所有搜索结果都请求全文。

## 快速参考

```bash
# 初始化（首次使用或 workspace 不存在时）
ph init

# 搜索论文（默认保存到 session 文件）
ph paper search "transformer attention mechanism" --max-items 10

# 直接输出 JSON（便于 agent 处理）
ph paper search "diffusion models" --output-format json

# 带过滤条件搜索
ph paper search "diffusion models" \
  --source arxiv \
  --year-from 2022 --year-to 2024 \
  --author "Ho" \
  --venue "NeurIPS" \
  --sort-by date \
  --max-items 20

# 查看本地缓存的论文
ph paper list

# 获取 L2 全文（需要 MINERU_API_KEY）
ph paper fetch-fulltext arxiv://1706.03762
ph paper fetch-fulltext arxiv://1706.03762 doi://10.xxx/yyy  # 支持多篇
```

## URI Scheme（必须使用）

引用论文时必须使用 URI scheme 格式，裸 ID 会被拒绝：

| 来源 | 格式 | 示例 |
|------|------|------|
| arXiv | `arxiv://ID` | `arxiv://1706.03762` |
| DOI | `doi://DOI` | `doi://10.1145/3340531` |
| DBLP | `dblp://path` | `dblp://conf/acl/...` |
| OpenReview | `openreview://forum_id` | `openreview://abc123` |
| ACL Anthology | `acl://anthology_id` | `acl://P19-1001` |
| Semantic Scholar | `s2://id` | `s2://204e3073870fae3d05` |

## 可用数据源（--source）

`arxiv` / `dblp` / `openreview` / `acl_anthology` / `serpapi`

不指定时由 `ph` 自动选择合适数据源。

## 标准工作流

### Step 1：确认 workspace 已初始化

如果这是首次运行或遇到 workspace 相关错误，先执行：

```bash
ph init
```

### Step 2：搜索论文（L1）

根据用户需求构造搜索命令。建议使用 `--output-format json` 直接获取结构化数据，便于处理：

```bash
ph paper search "查询关键词" --max-items 10 --output-format json
```

输出结构示例：

```json
{
  "ok": true,
  "data": {
    "papers": [
      {
        "id": "arxiv://1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, A.", "..."],
        "abstract": "...",
        "year": 2017,
        "venue": "NeurIPS",
        "url": "https://arxiv.org/abs/1706.03762"
      }
    ],
    "next_actions": [
      {
        "action": "fetch-fulltext",
        "hint": "使用 ph paper fetch-fulltext <id> 获取全文"
      }
    ]
  }
}
```

### Step 3：分析 L1 摘要，决定是否需要 L2

阅读每篇论文的摘要后，判断：

- 摘要已经能回答用户问题 → 不需要 L2，直接基于摘要回答
- 需要具体实现细节、实验数据、公式推导 → 对该论文请求 L2 全文

**不要对所有搜索结果都请求 L2**，只选择真正需要精读的论文（通常 1-3 篇）。

### Step 4：按需获取 L2 全文

```bash
ph paper fetch-fulltext arxiv://1706.03762
```

注意：
- 需要环境变量 `MINERU_API_KEY`
- 支持一次传入多个 URI
- 加 `--force-refresh` 强制重新解析（忽略缓存）
- 中文论文加 `--language ch`

### Step 5：综合分析，回答用户

结合 L1 摘要和 L2 全文（如有），给出有依据的回答。引用具体论文时附上 URI。

## 常见场景

### 场景 A：调研某个研究方向

```bash
# 搜索最近 2 年的相关工作，按日期排序
ph paper search "retrieval augmented generation" \
  --year-from 2023 \
  --sort-by date \
  --max-items 15 \
  --output-format json
```

只对最有价值的 1-2 篇获取全文，其余基于摘要总结。

### 场景 B：查找特定作者的论文

```bash
ph paper search "language model" --author "Karpathy" --max-items 10 --output-format json
```

### 场景 C：精读指定论文

用户提供了论文 ID 或 URL，直接获取 L2 全文：

```bash
ph paper fetch-fulltext arxiv://2305.10601
```

### 场景 D：查看已下载的论文

```bash
ph paper list
```

输出各论文的层级状态（L1/L2），便于了解本地缓存情况。

## 错误处理

| 错误码 | 含义 | 建议操作 |
|--------|------|----------|
| `E_NOT_FOUND` | 论文或资源不存在 | 确认 ID 正确，尝试换用其他数据源 |
| `E_INVALID_REF` | 引用格式无效 | 检查是否使用了 URI scheme（如 `arxiv://`） |
| `E_PROVIDER_FAILURE` | 外部数据源请求失败 | 检查网络，或加 `--debug-log` 查看详情 |

退出码含义：`0` 成功 / `2` 参数错误 / `3` 数据不存在 / `4` 上游失败 / `5` 部分成功

调试时加 `--debug-log` 参数：

```bash
ph --debug-log paper search "transformer" --max-items 3
```

## 注意事项

1. **`MINERU_API_KEY` 是可选的**：只有获取 L2 全文时才需要。如果用户没有配置，告知他们 L2 功能不可用，但 L1 搜索照常工作。
2. **每次搜索都会创建新的 session 文件**（默认 `--output-format file`），文件路径在输出中。
3. **`--source` 不指定时自动选择**，指定时确保使用正确的数据源名称（全小写）。
4. **论文 ID 区分大小写**，从搜索结果中复制 URI 时请保持原样。
5. **`fetch-fulltext` 是异步任务，耗时较长**：MinerU 在后端解析 PDF，通常需要数十秒至数分钟。命令会阻塞直到解析完成，期间不要认为是卡死。告知用户正在等待解析。
6. **国外 URL 网络限制**：MinerU 对 arXiv 等国外来源有网络限制，可能导致 `E_PROVIDER_FAILURE`。遇到此错误时先稍等再重试，而不是立即放弃。响应的 `notices` 字段会包含这两条提醒。
