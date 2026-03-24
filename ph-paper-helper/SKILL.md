---
name: ph-paper-helper
description: 使用 paper-helper (ph) CLI 进行学术论文检索、导入与渐进式阅读。当 agent 需要搜索论文、调研研究方向、导入指定论文、获取完整 metadata、或精读全文时使用。覆盖完整工作流：快路径（search/add）→ 慢路径（fetch）→ SQL 查询本地库。适用场景包括"帮我找关于 X 的论文"、"调研 Y 方向的工作"、"精读这篇论文"、"搜索 Z 作者的研究"、"查一下本地收录了哪些论文"。
---

# ph-paper-helper

使用 `ph`（paper-helper）CLI 进行学术论文检索、导入与渐进式阅读的完整操作指南。
alias ph='uv run --project ~/project/ph2 ph'

## 核心概念：快路径 vs 慢路径

`ph` 把操作分为两条路径：

| 路径 | 命令 | 速度 | 内容 |
|------|------|------|------|
| **快路径** | `ph search` / `ph add` | 快 | 基础 metadata（标题、摘要、作者、arXiv 字段），`metadata_state=basic` |
| **慢路径** | `ph fetch` | 慢（异步） | 完整 metadata 补全（多源 pipeline）+ MinerU PDF 全文解析 |

**原则**：先用快路径大量筛选，再对少数目标论文走慢路径深度补全。不要对所有搜索结果都调用 `fetch`。

## 命令速查

```bash
# 搜索论文（快路径，保存到本地 DB）
ph search --query "transformer attention mechanism" --max-results 10

# 从 URI 导入指定论文（快路径）
ph add --input arxiv://1706.03762
ph add --input doi://10.1145/3340531 --input arxiv://2010.11929

# 完整 metadata 补全 + MinerU 全文解析（慢路径，异步）
ph fetch --paper-id arxiv://1706.03762
ph fetch --paper-id arxiv://1706.03762 --include-content  # 完成后内联返回全文

# 查询本地数据库（只读 SQL）
ph sql --query "SELECT paper_id, title, metadata_state, fetch_state FROM papers ORDER BY created_at DESC LIMIT 10"

# 查看命令结构定义
ph schema --topic fetch
ph fetch --help
```

## URI Scheme（必须使用）

引用论文时必须使用 URI scheme，裸 ID 会触发 `E_UNKNOWN_REF_SCHEME`：

| 来源 | 格式 | 示例 |
|------|------|------|
| arXiv | `arxiv://ID` 或 `arxiv://IDvN` | `arxiv://1706.03762`、`arxiv://2301.00001v5` |
| DOI | `doi://DOI` | `doi://10.1145/3025453` |
| 网页 URL | `url://https://...` | `url://https://arxiv.org/abs/1706.03762` |
| 标题文本 | `title://标题` | `title://Attention Is All You Need` |
| 本地文件 | `file:///path/to/paper.pdf` | `file:///tmp/paper.pdf` |

## 标准工作流

### Step 1：搜索论文（快路径）

```bash
# 基础搜索（目前仅支持 arxiv provider）
ph search --query "diffusion models generative" --max-results 15

# 指定排序方式
ph search --query "vision transformer" --sort-by submittedDate --sort-order desc --max-results 20
```

输出示例（`--output-format json` 为默认）：

```json
{
  "schema_version": "ph_search_v1",
  "command": "search",
  "summary": "Found 3 papers from arxiv; upserted 3 basic records",
  "result": [
    {
      "paper_id": "arxiv://1706.03762v5",
      "title": "Attention Is All You Need",
      "authors": "Ashish Vaswani, Noam Shazeer, ...",
      "abstract": "...",
      "published_at": "2017-06-12",
      "metadata_state": "basic",
      "fetch_state": "none"
    }
  ],
  "errors": []
}
```

### Step 2：分析摘要，决定是否需要完整处理

阅读 `abstract` 后判断：

- 摘要已能回答用户问题 → 基于 basic 信息直接回答，无需继续
- 需要具体实验数据、完整方法、精确引用 → 对该论文调用 `fetch`

通常只对 1-3 篇核心论文调用 `fetch`，而非批量处理所有搜索结果。

### Step 3：完整处理（慢路径，异步）

`fetch` 是异步任务，每次调用都返回当前状态，需轮询直到 `fetch_state=done`。

**首次触发**（自动 add + 启动 pipeline）：

```bash
ph fetch --paper-id arxiv://1706.03762
```

```json
{
  "schema_version": "ph_fetch_v1",
  "result": [{
    "paper_id": "arxiv://1706.03762v5",
    "auto_add": {"triggered": true, "add_state": "done"},
    "fetch_state": "pending",
    "metadata_state": "running",
    "metadata_stage": "pms",
    "mineru_task_id": "a90e6ab6-..."
  }]
}
```

**轮询（重复调用相同命令）**：

```bash
ph fetch --paper-id arxiv://1706.03762
```

状态机：`fetch_state: none → pending → done | failed`

**完成后获取全文**：

```bash
ph fetch --paper-id arxiv://1706.03762 --include-content
```

等待期间（通常数十秒到数分钟）不要认为是卡死，MinerU 在后端解析 PDF 属正常耗时。

### Step 4：查询本地数据库

用 `ph sql` 可以直接查询已收录论文的状态和字段：

```bash
# 查看最近入库的论文
ph sql --query "SELECT paper_id, title, metadata_state, fetch_state FROM papers ORDER BY created_at DESC LIMIT 10"

# 查找全文已完成的论文
ph sql --query "SELECT paper_id, title, full_text_path FROM papers WHERE fetch_state = 'done'"

# 查看 metadata 补全情况
ph sql --query "SELECT paper_id, metadata_state, missing_fields_json FROM papers WHERE metadata_state != 'complete'"
```

只支持只读 SQL（SELECT / WITH / EXPLAIN QUERY PLAN），写操作会触发 `E_SQL_NOT_READONLY`。

## 常见场景

### 场景 A：调研某个研究方向

```bash
# 搜索最近的相关工作，按时间排序
ph search --query "retrieval augmented generation" \
  --sort-by submittedDate --sort-order desc \
  --max-results 15

# 对最重要的 1-2 篇做完整处理
ph fetch --paper-id arxiv://2005.11401
```

### 场景 B：导入指定论文

用户提供了论文 ID、DOI 或标题：

```bash
# 快速入库（不触发完整处理）
ph add --input arxiv://2310.06825
ph add --input doi://10.1145/3025453.3025575
ph add --input title://Attention Is All You Need

# 直接全量处理（自动先 add 再 fetch）
ph fetch --paper-id arxiv://2310.06825
```

### 场景 C：精读全文

```bash
# 触发全文解析并内联返回（完成后）
ph fetch --paper-id arxiv://1706.03762 --include-content
```

### 场景 D：批量导入后查看状态

```bash
# 批量导入
ph add --input arxiv://2301.00001 --input arxiv://2302.00002 --input doi://10.1145/xxx

# 查看导入状态
ph sql --query "SELECT paper_id, metadata_state, fetch_state FROM papers ORDER BY id DESC LIMIT 5"
```

### 场景 E：重新处理（忽略缓存）

```bash
ph fetch --paper-id arxiv://1706.03762 --force
```

## 全局参数

所有命令支持以下全局参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output-format` | `json` \| `jsonl` \| `tsv` \| `text` | `json` |
| `--quiet` | 抑制 stderr | false |
| `--verbose` | 输出详细执行日志到 stderr | false |
| `--timeout-seconds` | 单次操作超时秒数 | 30 |
| `--dry-run` | 预检副作用，不写入 DB 或文件 | false |

调试时用 `--verbose`：

```bash
ph --verbose search --query "transformer" --max-results 3
```

## 错误处理

| 错误码 | 退出码 | 含义 | 建议操作 |
|--------|--------|------|----------|
| `E_UNKNOWN_REF_SCHEME` | 2 | URI scheme 不支持 | 使用 `arxiv://`、`doi://`、`url://`、`title://`、`file://` |
| `E_PARAM_INVALID` | 2 | 参数类型错误（如 `PH_TIMEOUT_SECONDS` 非整数） | 检查环境变量类型 |
| `E_PARAM_INVALID_ENUM` | 2 | 枚举值非法 | 查看 `--help` 确认合法值 |
| `E_UNKNOWN_PARAM` | 2 | 未知参数 | 检查参数拼写，`ph` 不静默忽略未知参数 |
| `E_SQL_NOT_READONLY` | 2 | SQL 包含写操作 | 只用 SELECT/WITH/EXPLAIN |
| `E_DATA_NOT_FOUND` | 3 | 论文不存在 | 先用 `ph add` 导入，或直接用 `ph fetch` |
| `E_SOURCE_ALL_MISS` | 3 | 所有 metadata 源均未命中 | 调整 `--preset` 或检查网络 |
| `E_UPSTREAM_FAILURE` | 4 | 外部数据源请求失败 | 检查网络，稍后重试 |
| `E_UPSTREAM_TIMEOUT` | 4 | 外部数据源超时 | 调整 `--timeout-seconds` |
| `E_MINERU_TASK_FAILED` | 4 | MinerU 解析失败 | 检查 PDF 可访问性，检查 `PH_MINERU_TOKEN` |
| `E_PARTIAL_SUCCESS` | 5 | 批量操作部分失败 | 查看 `errors` 数组 |

退出码语义：`0` 成功 / `2` 参数错误 / `3` 数据不存在 / `4` 上游失败 / `5` 部分成功

## 环境变量

| 变量 | 说明 |
|------|------|
| `PH_DATA_DIR` | DB 和缓存根目录（默认 `~/.local/share/ph`） |
| `PH_MINERU_TOKEN` | MinerU token（只能通过环境变量或配置文件设置，禁止 flag 传入） |
| `PH_TIMEOUT_SECONDS` | 默认超时秒数（必须是整数，否则返回 `E_PARAM_INVALID`） |
| `PH_PRESET` | `fetch` 默认 metadata preset |

`PH_MINERU_TOKEN` 仅在执行 `ph fetch` 获取全文时需要。未配置时，search/add/sql 照常工作，fetch 的 metadata 补全部分也照常工作，只有 MinerU 全文解析阶段会失败。

## 注意事项

1. **`ph search` 目前仅支持 `--provider arxiv`**，其他 provider 会触发 `E_PARAM_INVALID_ENUM`。
2. **`ph fetch` 是幂等的**：`fetch_state=done` 且无 `--force` 时直接返回已有结果，不重复提交。
3. **MinerU 解析耗时较长**：通常数十秒到数分钟，命令会阻塞直到解析完成或超时，期间正常等待。
4. **国外网络限制**：MinerU 解析 arXiv 等国外 PDF 时可能遇到网络问题；遇 `E_MINERU_TASK_FAILED` 先稍等再重试。
5. **`ph add` 不触发 metadata 补全**：只做基础入库，完整 metadata 和全文需要再调用 `ph fetch`。
6. **本地 DB 路径**：`$PH_DATA_DIR/ph.db`（默认 `~/.local/share/ph/ph.db`），可用 `ph sql` 直接查询。
7. **旧命令已废弃**：`ph paper search`、`ph paper fetch-fulltext`、`ph init` 等旧式命令不再存在，请使用新命令树。
