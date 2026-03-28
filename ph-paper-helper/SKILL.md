---
name: ph-paper-helper
description: 使用 paper-helper (ph) CLI 进行学术论文检索、导入与渐进式阅读。当 agent 需要搜索论文、调研研究方向、导入指定论文、获取完整 metadata、或精读全文时使用。覆盖完整工作流：需求澄清 → 查询构造 → 快路径（search/add）→ 慢路径（fetch）→ SQL 查询本地库。适用场景包括"帮我找关于 X 的论文"、"调研 Y 方向的工作"、"精读这篇论文"、"搜索 Z 作者的研究"、"查一下本地收录了哪些论文"。
---

# ph-paper-helper

使用 `ph`（paper-helper）CLI 进行学术论文检索、导入与渐进式阅读。

```bash
alias ph='uv run --project ~/project/ph2 ph'
```

## 场景路由

先判断用户意图属于哪一类，再进入对应流程：

1. **搜索论文 / 调研方向**：用户想找某个主题、作者、领域的论文
   → 进入「搜索工作流」
2. **导入已知论文**：用户给出了具体的 arXiv ID、DOI 或标题
   → 直接使用 `ph add` 或 `ph fetch`，参考「快速导入」
3. **精读全文**：用户想深入阅读某篇已导入的论文
   → 使用 `ph fetch --include-content`，参考「慢路径」
4. **查询本地库**：用户想了解已收录论文的状态
   → 使用 `ph sql`，参考「本地查询」

不确定时先问用户。不要同时走多条路径。

---

## 搜索工作流（核心）

搜索是使用频率最高的场景。`ph search` 底层调用 arXiv API，查询质量直接决定结果质量。因此搜索前必须先理解用户需求，再构造精确查询。

### Step 1：需求澄清

收到搜索请求后，不要立刻执行。先从用户的话中提取以下信息：

| 维度 | 要搞清楚的 | 示例 |
|------|-----------|------|
| **主题** | 用户关心的核心概念是什么？ | "diffusion model 用于图像编辑" |
| **目的** | 调研综述？找具体方法？对比方案？ | "想了解最新进展" vs "找能用的baseline" |
| **范围** | 有没有偏好的子领域/类别？ | "只看 CV 方向的" → `cat:cs.CV` |
| **作者** | 有没有特定作者？ | "Kaiming He 的工作" → `au:he` |
| **时间** | 有没有时间偏好？ | "最近一年的" → `--sort-by submittedDate` |
| **数量** | 需要广泛调研还是快速找几篇？ | 广泛 → `--max-results 20`；快速 → 5 |

**判断规则**：

- 如果用户的请求已经足够清晰（如"搜 attention is all you need"），直接执行，不追问。
- 如果请求模糊（如"帮我找些论文"、"调研一下 LLM"），则追问 1-2 个关键问题来缩小范围。
- 追问要简洁具体，不要列出长长的问题清单。选择对查询构造影响最大的 1-2 个维度追问即可。

**追问示例**：

> 用户："帮我找 diffusion model 的论文"
> → "你更关注 diffusion model 的哪个方面？比如图像生成、视频生成、3D、加速采样？另外需要最新的还是经典的都行？"

> 用户："搜一下 RL 在机器人上的应用"
> → "需要侧重 sim-to-real transfer、manipulation 还是 locomotion？我可以针对性地搜。"

### Step 2：构造查询

arXiv API 支持字段限定和布尔组合，善用这些能力能大幅提升结果质量。

**查询构造规则**：

读取 `references/arxiv-query-syntax.md` 了解完整语法。核心原则：

1. **用英文关键词**：arXiv 是英文数据库
2. **用字段限定缩小范围**：`ti:` 限标题、`au:` 限作者、`cat:` 限类别、`abs:` 限摘要
3. **用 AND 组合多个条件**：`ti:diffusion AND cat:cs.CV`
4. **用 OR 覆盖同义表达**：`ti:(transformer OR attention)`
5. **不要过度限定**：arXiv 搜索不够智能，关键词太多反而漏掉结果。2-4 个核心术语为宜
6. **主题宽泛时用 `all:`**，精确找某篇时用 `ti:`

**常见查询模板**：

```bash
# 主题搜索：用核心术语 + 类别限定
ph search --query "ti:diffusion AND ti:editing AND cat:cs.CV" --max-results 15

# 作者搜索：au + 可选主题
ph search --query "au:hinton AND ti:distillation" --max-results 10

# 最新进展：按提交时间降序
ph search --query "abs:large language model reasoning" --sort-by submittedDate --sort-order desc --max-results 20

# 找特定论文：精确标题词
ph search --query "ti:attention AND ti:all AND ti:need" --max-results 5
```

### Step 3：执行搜索

```bash
ph search --query "<构造好的查询>" --max-results <数量> [--sort-by submittedDate --sort-order desc]
```

### Step 4：结果分析与迭代

搜索返回后：

1. **阅读摘要**，筛选出与用户需求匹配的论文
2. **向用户呈现筛选结果**：给出简要的论文列表（标题 + 一句话总结 + 相关度判断）
3. **判断是否需要调整查询**：
   - 结果太少 → 放宽查询（减少限定词、用 OR 增加同义词）
   - 结果不相关 → 换关键词或加限定
   - 用户需要更多 → 增大 `--max-results` 或换角度再搜
4. **引导下一步**：问用户是否需要对某些论文做深入阅读（fetch）

**不要**对所有搜索结果都调用 `fetch`。通常只对 1-3 篇核心论文走慢路径。

---

## 快速导入

用户提供了明确的论文标识时，跳过搜索直接导入：

```bash
# 快路径：只入库基础信息
ph add --input arxiv://1706.03762
ph add --input doi://10.1145/3340531
ph add --input arxiv://2301.00001 --input arxiv://2302.00002  # 批量

# 直接走完整处理（自动 add + fetch）
ph fetch --paper-id arxiv://1706.03762
```

### URI Scheme（必须使用）

| 来源 | 格式 | 示例 |
|------|------|------|
| arXiv | `arxiv://ID` 或 `arxiv://IDvN` | `arxiv://1706.03762`、`arxiv://2301.00001v5` |
| DOI | `doi://DOI` | `doi://10.1145/3025453` |
| 网页 URL | `url://https://...` | `url://https://arxiv.org/abs/1706.03762` |
| 标题文本 | `title://标题` | `title://Attention Is All You Need` |
| 本地文件 | `file:///path/to/paper.pdf` | `file:///tmp/paper.pdf` |

裸 ID 会触发 `E_UNKNOWN_REF_SCHEME`。

---

## 慢路径（fetch）

`fetch` 执行完整 metadata 补全 + MinerU PDF 全文解析。它是异步的，需要轮询。

```bash
# 触发（自动先 add 再 fetch）
ph fetch --paper-id arxiv://1706.03762

# 轮询（重复相同命令，直到 fetch_state=done）
ph fetch --paper-id arxiv://1706.03762

# 完成后获取全文
ph fetch --paper-id arxiv://1706.03762 --include-content

# 强制重新处理
ph fetch --paper-id arxiv://1706.03762 --force
```

状态机：`fetch_state: none → pending → done | failed`

MinerU 解析通常耗时数十秒到数分钟，期间正常等待，不要认为卡死。

---

## 本地查询

用 `ph sql` 查询已收录论文（只读 SQL）：

```bash
# 最近入库
ph sql --query "SELECT paper_id, title, metadata_state, fetch_state FROM papers ORDER BY created_at DESC LIMIT 10"

# 已完成全文解析的
ph sql --query "SELECT paper_id, title FROM papers WHERE fetch_state = 'done'"

# 按标题模糊搜索
ph sql --query "SELECT paper_id, title FROM papers WHERE title LIKE '%transformer%'"
```

---

## 错误处理

| 错误码 | 含义 | 处理 |
|--------|------|------|
| `E_UNKNOWN_REF_SCHEME` | URI scheme 不对 | 用 `arxiv://`、`doi://` 等 |
| `E_PARAM_INVALID_ENUM` | 枚举值非法 | 检查 `--help` |
| `E_DATA_NOT_FOUND` | 论文不存在 | 先 `add` 或直接 `fetch` |
| `E_SOURCE_ALL_MISS` | 所有源均未命中 | 检查 ID 是否正确 |
| `E_UPSTREAM_FAILURE` | 外部源失败 | 检查网络，稍后重试 |
| `E_UPSTREAM_TIMEOUT` | 超时 | 增大 `--timeout-seconds` |
| `E_MINERU_TASK_FAILED` | MinerU 失败 | 检查 PDF 可访问性和 token |

退出码：`0` 成功 / `2` 参数错误 / `3` 数据不存在 / `4` 上游失败 / `5` 部分成功

## 环境变量

| 变量 | 说明 |
|------|------|
| `PH_DATA_DIR` | DB 根目录（默认 `~/.local/share/ph`） |
| `PH_MINERU_TOKEN` | MinerU token（仅 fetch 全文时需要） |
| `PH_TIMEOUT_SECONDS` | 默认超时秒数 |
| `PH_PRESET` | fetch 默认 metadata preset |

## 全局参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output-format` | `json`/`jsonl`/`tsv`/`text` | `json` |
| `--quiet` | 抑制 stderr | false |
| `--verbose` | 详细日志 | false |
| `--timeout-seconds` | 超时秒数 | 30 |
| `--dry-run` | 预检不写入 | false |
