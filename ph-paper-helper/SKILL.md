---
name: ph-paper-helper
description: 使用 paper-helper (ph) CLI 进行学术论文检索、导入、BibTeX 导出与渐进式阅读。当 agent 需要搜索论文、调研研究方向、导入指定论文、获取完整 metadata、导出 BibTeX 参考文献、或精读全文时使用。覆盖完整工作流：需求澄清 → 查询构造 → 快路径（search/add）→ 慢路径（fetch）→ SQL 查询本地库。适用场景包括"帮我找关于 X 的论文"、"调研 Y 方向的工作"、"导入指定论文"、"获取完整 metadata"、"导出 BibTeX"、"精读全文"、"搜索 Z 作者的研究"、"查一下本地收录了哪些论文"。
---

# ph-paper-helper

使用 `ph`（paper-helper）CLI 进行学术论文检索、导入、BibTeX 导出与渐进式阅读。

```bash
alias ph='uv run --project ~/project/ph2 ph'
```

## 场景路由

先判断用户意图属于哪一类，再进入对应流程：

1. **搜索论文 / 调研方向**：用户想找某个主题、作者、领域的论文
   → 进入「搜索工作流」
2. **导入已知论文**：用户给出了具体的 arXiv ID、DOI 或标题
   → 直接使用 `ph import` 或 `ph add --bib`，参考「快速导入」
3. **添加到 BibTeX**：用户需要将论文写入 .bib 文件
   → 使用 `ph add --bib`，参考「BibTeX 写入」
4. **精读全文**：用户想深入阅读某篇已导入的论文
   → 使用 `ph fetch --include-content`，参考「慢路径」
5. **查询本地库**：用户想了解已收录论文的状态
   → 使用 `ph sql`，参考「本地查询」

不确定时先问用户。不要同时走多条路径。

---

## 搜索工作流（核心）

`ph search` 默认使用 Semantic Scholar API（需 API key），也可通过 `--source arxiv` 切换到 arXiv API（无需 key，仅覆盖 arXiv 论文）。查询质量直接决定结果质量，因此搜索前必须先理解用户需求，再构造精确查询。

### Step 1：需求澄清

收到搜索请求后，不要立刻执行。先从用户的话中提取以下信息：

| 维度 | 要搞清楚的 | 示例 |
|------|-----------|------|
| **主题** | 用户关心的核心概念是什么？ | "diffusion model 用于图像编辑" |
| **目的** | 调研综述？找具体方法？对比方案？ | "想了解最新进展" vs "找能用的baseline" |
| **范围** | 有没有偏好的子领域？ | "只看 CV 方向的" |
| **作者** | 有没有特定作者？ | "Kaiming He 的工作" |
| **数量** | 需要广泛调研还是快速找几篇？ | 广泛 → `--max-results 20`；快速 → 5 |
| **搜索源** | 是否需要切换到 arXiv？ | 仅 arXiv 论文 → `--source arxiv` |

**判断规则**：

- 如果用户的请求已经足够清晰（如"搜 attention is all you need"），直接执行，不追问。
- 如果请求模糊（如"帮我找些论文"、"调研一下 LLM"），则追问 1-2 个关键问题来缩小范围。
- 追问要简洁具体，不要列出长长的问题清单。选择对查询构造影响最大的 1-2 个维度追问即可。

### Step 2：构造查询

**默认使用 Semantic Scholar（`--source s2`）**：使用自然语言关键词组合，S2 会做语义匹配。

**查询构造规则**：

1. **用英文关键词**：学术论文数据库以英文为主
2. **核心术语组合即可**：S2 搜索支持自然语言，不需要布尔运算符
3. **2-5 个核心术语为宜**：太少结果太泛，太多可能遗漏
4. **如需精确查找 arXiv 论文**：加 `--source arxiv`，可使用 arXiv 字段限定语法（`ti:`, `au:`, `cat:`, `abs:`，AND/OR 组合），详见 `references/arxiv-query-syntax.md`

**常见查询模板**：

```bash
# 主题搜索（默认 S2）
ph search --query "diffusion model image editing" --max-results 15

# 作者 + 主题
ph search --query "Kaiming He knowledge distillation" --max-results 10

# 切换到 arXiv 搜索（支持字段限定语法）
ph search --source arxiv --query "ti:diffusion AND ti:editing AND cat:cs.CV" --max-results 15
```

### Step 3：执行搜索

```bash
ph search --query "<构造好的查询>" --max-results <数量> [--source arxiv]
```

### Step 4：结果分析与迭代

搜索返回后：

1. **阅读摘要**，筛选出与用户需求匹配的论文
2. **向用户呈现筛选结果**：给出简要的论文列表（标题 + 一句话总结 + 相关度判断）
3. **判断是否需要调整查询**：
   - 结果太少 → 放宽查询（减少关键词、换同义表达）
   - 结果不相关 → 换关键词角度
   - S2 结果不佳 → 尝试 `--source arxiv` 换源
4. **引导下一步**：问用户是否需要对某些论文做深入阅读（fetch），或直接添加到 .bib（add）

**不要**对所有搜索结果都调用 `fetch`。通常只对 1-3 篇核心论文走慢路径。

---

## 快速导入

用户提供了明确的论文标识时，跳过搜索直接导入：

```bash
# 全局导入（仅入库，不写 .bib）
ph import --input arxiv://1706.03762
ph import --input arxiv://2301.00001 --input arxiv://2302.00002  # 批量

# 导入并写入 .bib（推荐：一步完成 import + bib 补全 + 写入 .bib）
ph add --input arxiv://1706.03762 --bib refs.bib

# 直接走完整处理（自动 import + bib 补全 + 全文提取，不写 .bib）
ph fetch --paper-id arxiv://1706.03762
```

### URI Scheme（必须使用）

| 来源 | 格式 | 示例 |
|------|------|------|
| arXiv | `arxiv://ID` 或 `arxiv://IDvN` | `arxiv://1706.03762`、`arxiv://2301.00001v5` |
| DOI | `doi://DOI` | `doi://10.1145/3025453` |
| Semantic Scholar | `s2://HASH` | `s2://649def34f8be52c8b66281...` |

仅支持以上三种 scheme。裸 ID 会触发 `E_UNKNOWN_REF_SCHEME`。

### 跨 scheme 查找

DB 层支持任意 ID 反查。以 `doi://10.xxx` 入库的论文，用 `arxiv://yyy` 也能找到（只要它们是同一篇）。因此：

- 不需要记住论文是用哪个 scheme 入库的
- `ph add --input arxiv://xxx --bib refs.bib` 能识别已入库为 `doi://yyy` 的同一篇论文，不会重复调 API

---

## BibTeX 写入（add --bib）

`ph add` 是将论文写入 .bib 文件的主要命令。它一步完成：导入 → bib 元数据补全 → 写入 .bib。

```bash
# 添加单篇
ph add --input arxiv://1706.03762 --bib refs.bib

# 批量添加
ph add --input arxiv://1706.03762 --input doi://10.1145/3025453 --bib refs.bib

# 跳过元数据补全
ph add --input arxiv://1706.03762 --bib refs.bib --skip-metadata
```

### 三阶段 bib 元数据补全

`add` 默认执行三阶段补全（`--skip-metadata` 跳过）：

1. **S2 detail API** → venue, journal, volume, pages, abstract, citation_count
2. **Crossref**（仅有 DOI 时）→ publisher, pages, number, volume, pub_type
3. **arXiv API**（仅有 arxiv_id 时）→ primary_category, month, journal_ref

### bib_ready vs bib_usable

输出中有两个状态字段，含义不同：

| 字段 | 含义 | 判定条件 |
|------|------|----------|
| `bib_ready` | 正式发表的完整 metadata | title + authors + venue + year + 非预印本 |
| `bib_usable` | BibTeX 可用于引用 | title + authors + year（预印本也可为 true） |

对 arXiv 预印本：`bib_ready=false`（这是规则不是 bug）但 `bib_usable=true`（可以正常引用）。

### incomplete_reason

当 `bib_ready=false` 时，`incomplete_reason` 字段区分原因：

| 值 | 含义 | 需要处理吗 |
|----|------|-----------|
| `preprint` | 预印本，元数据实际已齐全 | 不需要，bib_usable=true 即可用 |
| `missing_fields:venue,year` | 关键字段缺失 | 可能需要手动补或重试 fetch |
| `upstream_failure:s2,crossref` | 上游 API 失败 | 稍后重试 |

### arXiv 预印本 BibTeX 格式

arXiv 预印本自动使用规范格式渲染：

```bibtex
@article{chen2026skillcraft,
  title = {SkillCraft: Can LLM Agents Learn to Use Tools Skillfully?},
  author = {Shiqi Chen and Jingze Gai},
  year = {2026},
  month = {2},
  journal = {arXiv preprint arXiv:2603.00718},
  eprint = {2603.00718},
  archiveprefix = {arXiv},
  primaryclass = {cs.CL},
  url = {https://arxiv.org/pdf/2603.00718},
}
```

已正式发表的论文（有 `journal_ref`）使用标准 `@article`/`@inproceedings` 格式。

### .bib 文件去重

每条 ph 管理的 entry 前有一行注释标记 paper_id，用于去重：

```bibtex
% paper_id: arxiv://2603.00718
@article{chen2026skillcraft,
  ...
}
```

- 再次 add 同一篇论文 → 用最新 metadata 覆盖更新（保留原 cite key）
- 手写的条目（没有 `% paper_id:` 注释）会被原样保留

---

## 慢路径（fetch）

`fetch` 执行三阶段 bib 补全 + MinerU PDF 全文解析。

```bash
# 触发（自动先 import 再 fetch）
ph fetch --paper-id arxiv://1706.03762

# 仅补全 bib 元数据，跳过全文提取
ph fetch --paper-id arxiv://1706.03762 --metadata-only

# 完成后获取全文
ph fetch --paper-id arxiv://1706.03762 --include-content

# 强制重新处理
ph fetch --paper-id arxiv://1706.03762 --force
```

状态机：`fetch_state: none → pending → done | failed`

MinerU 解析通常耗时数十秒到数分钟，重复相同命令轮询直到 `fetch_state=done`。

---

## 本地查询

用 `ph sql` 查询已收录论文（只读 SQL）：

```bash
# 最近入库
ph sql --query "SELECT paper_id, title, bib_ready, fetch_state FROM papers ORDER BY created_at DESC LIMIT 10"

# 按标题模糊搜索
ph sql --query "SELECT paper_id, title FROM papers WHERE title LIKE '%transformer%'"

# arXiv 预印本中 bib 可用的
ph sql --query "SELECT paper_id, title, primary_category FROM papers WHERE arxiv_id IS NOT NULL AND venue IS NOT NULL"

# bib 已补全的正式发表论文
ph sql --query "SELECT paper_id, title, venue, year FROM papers WHERE bib_ready = 1"
```

---

## 错误处理

| 错误码 | 含义 | 处理 |
|--------|------|------|
| `E_UNKNOWN_REF_SCHEME` | URI scheme 不对 | 用 `arxiv://`、`doi://`、`s2://` |
| `E_PARAM_REQUIRED` | 缺少必填参数 | 补充 `--input`、`--bib` 等 |
| `E_DATA_NOT_FOUND` | 论文不存在 | 先 `import` 或用 `add`（自动 import） |
| `E_UPSTREAM_FAILURE` | 外部源失败 | 检查网络，稍后重试 |
| `E_MINERU_TASK_FAILED` | MinerU 失败 | 检查 PDF 可访问性和 token |

退出码：`0` 成功 / `2` 参数错误 / `3` 数据不存在 / `4` 上游失败 / `5` 部分成功

## 环境变量

| 变量 | 说明 |
|------|------|
| `PH_DATA_DIR` | DB 根目录（默认 `~/.local/share/ph`） |
| `PH_S2_API_KEY` | Semantic Scholar API key（search 默认源需要） |
| `PH_MINERU_TOKEN` | MinerU token（仅 fetch 全文时需要） |
| `PH_TIMEOUT_SECONDS` | 默认超时秒数 |

## 全局参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--quiet` | 抑制 stderr | false |
| `--verbose` | 详细日志 | false |
| `--timeout-seconds` | 超时秒数 | 30 |
| `--dry-run` | 预检不写入 | false |
