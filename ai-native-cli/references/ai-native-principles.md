# AI-Native CLI 设计原则

**副标题：Deterministic CLI for Agents — 可预测、可验证、可管道，不靠猜**

---

## 0. 什么是 AI-Native CLI

AI-Native CLI 是一类**以 agent（AI 代理）为第一公民用户**设计的命令行工具。它不是传统 CLI 加个 `--json` 就完事，而是在命名、参数、输出、错误处理、文档、可组合性等每一个层面都为机器消费做了专门设计。

**工具本身不内置任何 AI 能力。** 它是一把精密的手术刀，专门为 agent 提供确定性的数据操作和信息检索接口——AI 的智能在调用者（agent）那侧，工具这侧只负责把每一步做得精准、可预测、可组合。

核心信条：**agent 不猜，agent 声明；agent 不看，agent 解析；agent 不问，agent 查。**

---

## 1. 命名与参数：消灭歧义

### 1.1 参数必须用长名，禁止默认短名

短参数是为人类记忆设计的快捷方式，但对 agent 来说它只会引入歧义和误用。

```bash
# ✗ 不要这样
mycli -p 10.1234/xxxx -f json

# ✓ 应该这样
mycli paper info --paper-id "10.1234/xxxx" --output-format json
```

如果确实需要兼顾人类使用体验，可以在 human-mode 下启用短参数，但 agent 调用路径中短参数应当被视为未知参数而报错。

### 1.2 参数名自描述，避免缩写

参数名要能让 agent 仅凭名称就判断语义和类型，无需翻阅文档。

```bash
# ✗ 含义不明
--fmt json --src arxiv --m exact

# ✓ 一目了然
--output-format json --source arxiv --match-mode exact
```

命名建议遵循 `<对象>-<属性>` 或 `<动作>-<修饰>` 的模式，如 `--paper-id`、`--target-language`、`--sort-order`。

### 1.3 显式声明输入类型，不靠推断

永远不要让命令去"猜"用户给的是 DOI 还是 URL 还是标题。推荐使用 **URI scheme** 将类型直接编码进值本身——单一参数，自描述，零歧义。

```bash
# ✗ 命令自己猜输入类型
mycli paper add "10.1234/xxxx"

# ✗ 类型和值拆成两个参数，冗余且易错位
mycli paper add --id-kind doi --id-value "10.1234/xxxx"

# ✓ URI scheme：类型即前缀，一个参数表达完整意图
mycli paper add --paper-ref doi://10.1234/xxxx
mycli paper add --paper-ref arxiv://2301.00001
mycli paper add --paper-ref s2://abc123def456
mycli paper add --paper-ref https://arxiv.org/abs/2301.00001
```

URI scheme 的好处：scheme 本身就是类型声明，agent 生成参数时不需要同时维护两个字段的一致性；工具校验时只需解析 scheme 前缀，格式非法直接报错。

批量输入时，每条记录同样使用单字段：

```json
{"paper_ref": "doi://10.1234/xxxx"}
{"paper_ref": "arxiv://2301.00001"}
{"paper_ref": "https://arxiv.org/abs/2301.00001"}
```

支持的 scheme 必须在文档中穷举，不接受未知 scheme 并给出明确错误：

```json
{
  "error_code": "E_UNKNOWN_REF_SCHEME",
  "message": "Unsupported scheme 'isbn' in paper-ref 'isbn://978-3-16-148410-0'",
  "supported_schemes": ["doi", "arxiv", "s2", "https", "http"]
}
```

### 1.4 命令名体现约束和资源

命令名应当是 `<资源> <动作>` 的结构，而不是模糊的动词。并且约束条件（输入输出格式、实现方式、数据源等）全部通过 flag 显式表达。

```bash
# 顶层是资源，二级是动作
mycli paper add
mycli paper info
mycli paper search
mycli paper list
mycli paper abstract
mycli paper export
```

---

## 2. 输入输出：强类型、结构化、可版本化

### 2.1 输入输出格式必须可声明

每个命令都应支持以下通用 flag：

```
--json           输出 JSON（布尔开关，主要输出格式）
--json field1,field2  字段选择输出（不带字段时输出完整对象）
--output-format  jsonl | tsv | text（需要非 JSON 格式时使用）
--input <文件路径或 - 表示 stdin>
--input-format  jsonl | json | tsv | plain
--output <文件路径或 stdout>
```

`--json` 是主要输出开关，与 `gh`、`kubectl` 等成熟 CLI 对齐；`--output-format` 用于选择 jsonl/tsv/text 等其他格式。默认行为是人类可读文本，`--json` 开关后输出 JSON。

### 2.2 输出 schema 固定且可版本化

每条输出结果都应包含以下元信息：

```json
{
  "schema_version": "paper_info_v1",
  "command": "paper info",
  "timestamp": "2026-03-10T12:00:00Z",
  "result": [ ... ],
  "errors": [ ... ]
}
```

并且提供 schema 查询命令：

```bash
mycli schema show --name paper_info_v1
```

Agent 可以在调用前先查 schema，确认字段结构，再动态生成后续管道逻辑。

### 2.3 text 模式是结构化的"视图"，不是另一种数据

`--output-format text` 只是对同一份结构化数据的人类可读渲染，不应包含任何在 json 输出中不存在的信息，也不应遗漏任何关键字段。

---

## 3. 退出码：严格语义化

退出码是 agent 判断命令执行结果的第一信号。必须语义明确、互斥、稳定。

| 退出码 | 含义 | 说明 |
|--------|------|------|
| 0 | 成功 | 所有操作完成，无错误 |
| 1 | 通用错误 | 未分类的运行时错误 |
| 2 | 参数错误 | 参数缺失、类型错误、组合冲突 |
| 3 | 数据不存在 | 请求的资源在任何源中均未找到 |
| 4 | 上游源失败 | 网络错误、API 超时、第三方服务不可用 |
| 5 | 部分成功 | 批量操作中有部分项失败 |

补充原则：

- 退出码必须在文档中明确列出，不能只写"非零表示失败"。
- `--strict` 模式下，任何非致命错误（如部分成功）也应以非 0 退出。
- 退出码应保持跨版本稳定，新增码值不复用旧码。

---

## 4. 搜索与过滤：可预测，不做"智能"

### 4.1 不用语义搜索，用 grep 路线

语义搜索的结果不可预测、不可解释、不可复现。AI-Native CLI 的搜索应该像 grep 一样确定性。

```bash
# 本地全文搜索
mycli paper search \
  --query "diffusion model" \
  --field title \
  --match-mode contains \
  --source local

# 结合 Unix 工具
mycli paper list --output-format tsv | grep -i "transformer"
mycli paper list --output-format jsonl | jq '.title'
```

### 4.2 搜索参数要穷举约束

```
--source         arxiv | semantic_scholar | google_scholar | local
--match-mode     exact | contains | regex
--field          title | abstract | author | all
--sort-by        published_at | citation_count | title
--sort-order     asc | desc
--max-items      <number>
```

绝不出现"智能排序""相关度排序"这种模糊词——如果非要有相关度，那就叫 `--sort-by bm25_score` 并文档说明算法。

### 4.3 过滤器可组合

多个过滤条件之间的关系必须显式声明：

```bash
mycli paper list \
  --filter-field year --filter-op gte --filter-value 2023 \
  --filter-field citation_count --filter-op gte --filter-value 10 \
  --filter-logic and
```

或者接受结构化的过滤表达式输入：

```bash
echo '{"and": [{"field":"year","op":"gte","value":2023}, {"field":"citation_count","op":"gte","value":10}]}' \
| mycli paper list --filter-input - --filter-input-format json
```

---

## 5. 管道与组合：与 Unix 工具链天然协作

### 5.1 stdin/stdout/stderr 的使用规约

这是 AI-Native CLI 作为良好 Unix 公民的基础协议：

- **stdin**：读取批量输入数据（当 `--input -`）
- **stdout**：仅输出结果数据，不混杂日志和提示信息
- **stderr**：仅输出错误信息和运行日志
- 永远不依赖交互式输入（如 `readline`、`prompt`）

### 5.2 通用控制 flag

每个命令都应支持以下管道友好的控制参数：

```
--quiet          抑制所有 stderr 输出
--verbose        输出详细执行日志到 stderr
--log-format     jsonl | text（日志格式，默认 text）
--no-network     仅查本地数据，不发起任何网络请求
--timeout-seconds <number>
--max-items      <number>（限制输出条数）
--strict         遇到任何非致命错误即以非 0 退出
```

### 5.3 典型管道用法示例

```bash
# 批量添加论文并提取内部 ID
cat refs.jsonl \
| mycli paper add --input - --input-format jsonl --output-format jsonl \
| jq -r '.result[].paper_id' \
| xargs -I {} mycli paper abstract --paper-id {} --output-format text

# refs.jsonl 的格式：
# {"paper_ref": "doi://10.1234/xxxx"}
# {"paper_ref": "arxiv://2301.00001"}

# 筛选后导出
mycli paper list --output-format tsv \
| awk -F'\t' '$3 >= 2023' \
| mycli paper export --input - --input-format tsv --output papers.bib
```

### 5.4 幂等性与可复跑

- 相同输入 + 相同参数 = 相同输出（除时间戳等元信息外）。
- `add` 操作对已存在数据应返回成功但标注 `"status": "already_exists"`，而不是报错。
- 提供 `--dry-run` 让 agent 预检操作效果。

---

## 6. 错误处理：机器可消费的错误信息

### 6.1 错误输出结构化

错误信息不是给人读的字符串，而是给 agent 解析的结构化数据。

默认错误输出：

```json
{
  "error_code": "E_UNKNOWN_REF_SCHEME",
  "message": "Unsupported scheme 'isbn' in --paper-ref value",
  "fix_hint": "Use one of the supported schemes: doi://, arxiv://, s2://, https://"
}
```

`--error-detail full` 时扩展：

```json
{
  "error_code": "E_UNKNOWN_REF_SCHEME",
  "message": "Unsupported scheme 'isbn' in --paper-ref value",
  "fix_hint": "Use one of the supported schemes: doi://, arxiv://, s2://, https://",
  "field_path": "$.paper_ref",
  "received_value": "isbn://978-3-16-148410-0",
  "supported_schemes": ["doi", "arxiv", "s2", "https", "http"],
  "example_fix": "--paper-ref doi://10.1234/xxxx",
  "schema_ref": "paper_add_input_v1"
}
```

### 6.2 错误码全局唯一且文档化

每个错误码应当是可 grep 的字符串（不是数字），并可通过 CLI 查询：

```bash
mycli explain-error --code E_UNKNOWN_REF_SCHEME
```

输出该错误的含义、常见原因、修复建议、相关命令。

### 6.3 上游状态透明

当命令依赖外部数据源时，结果中应包含每个源的状态：

```json
{
  "result": [ ... ],
  "source_status": [
    {"source": "arxiv", "status": "ok", "latency_ms": 342},
    {"source": "semantic_scholar", "status": "timeout", "latency_ms": 5000}
  ]
}
```

---

## 7. 文档：`--help` 标准行为 + `--help --full` 完整文档

### 7.1 文档是 agent 的 API

AI-Native CLI 的文档不是给人从头读到尾的教程。`--help` 是 agent 第一入口，应让 agent 仅凭二进制和一个模糊任务就知道该怎么调用这个命令。

### 7.2 两级帮助

```bash
# 第一级：标准 help（synopsis + flags + 一句话描述）
mycli paper add --help

# 第二级：完整文档（加上 examples + output schema + error codes）
mycli paper add --help --full

# 机器可读版本（agent 解析用）
mycli paper add --help --full --json
```

### 7.3 `--help` 应该回答的问题

每个命令的 `--help` 应该回答：

- 这个命令做什么？
- 必填参数有哪些？类型是什么？
- 可选参数有哪些？默认值是什么？
- 如何调用一个最小示例？

### 7.4 `--help --full` 应该提供的内容

```
COMMAND
  paper add — Add a paper to local library by reference URI

USAGE
  mycli --json paper add --paper-ref <uri> [flags]

FLAGS
  --paper-ref   uri  required  Paper reference (doi://, arxiv://, s2://, https://)
  --source      enum  local   arxiv | semantic_scholar | local
  --dry-run     bool  false   Preview without writing

OUTPUT SCHEMA
  {
    "paper_id": "string",
    "status": "created | already_exists",
    "title": "string",
    "source": "string"
  }

ERROR CODES
  E_UNKNOWN_REF_SCHEME  exit 2  Unsupported URI scheme
                                 Run: mycli --json paper add --help --full --json
  E_UPSTREAM_FAILURE    exit 4  Source API unavailable. Retry or use --source local

EXAMPLES
  # Basic add
  mycli --json paper add --paper-ref doi://10.1234/xxxx

  # Batch add from file
  cat refs.jsonl | mycli --json paper add --input - --input-format jsonl

  # Dry-run preview
  mycli --json paper add --paper-ref arxiv://2301.00001 --dry-run
```

### 7.5 `--help --full --json` 输出结构

Agent 可以解析这个输出来动态构建后续命令：

```json
{
  "command": "paper add",
  "synopsis": "Add a paper to local library by reference URI",
  "flags": [
    {
      "name": "--paper-ref",
      "type": "uri",
      "required": true,
      "supported_schemes": ["doi", "arxiv", "s2", "https"],
      "description": "Paper reference URI"
    }
  ],
  "output_schema": {
    "paper_id": "string",
    "status": "created | already_exists"
  },
  "error_codes": [
    {
      "code": "E_UNKNOWN_REF_SCHEME",
      "exit": 2,
      "description": "Unsupported URI scheme",
      "fix": "Use one of: doi://, arxiv://, s2://, https://"
    }
  ],
  "examples": [
    {
      "description": "Basic add",
      "command": "mycli --json paper add --paper-ref doi://10.1234/xxxx"
    }
  ]
}
```

---

## 8. 响应信息：细节富集，结构可裁剪

### 8.1 每次响应都是"完整报告"

Agent 不怕信息多，怕信息缺。每次命令的响应应当包含足够的上下文，使 agent 无需追加调用即可做出下一步决策。

建议每次响应都包含：

```json
{
  "schema_version": "...",
  "command": "...",
  "timestamp": "...",
  "summary": "Found 3 papers matching query",
  "result": [ ... ],
  "errors": [ ... ],
  "metadata": {
    "total_count": 42,
    "returned_count": 3,
    "has_more": true,
    "cursor": "abc123"
  },
  "next_actions": [
    "mycli paper info --paper-id <id> --output-format json",
    "mycli paper list --cursor abc123 --max-items 10"
  ],
  "refs": [
    {"topic": "paper.search", "section": "pagination"}
  ]
}
```

- **summary**：一句话结论，人看这个。
- **result / errors**：结构化数据，agent 解析这个。
- **next_actions**：可直接执行的后续命令建议。
- **refs**：指向相关文档节点，agent 按需拉取。

### 8.2 分页用 provider 实际提供的方式

分页使用 provider 实际提供的分页信息。`next_cursor`、`next_url`、`offset`、`page_count` 均可接受，如实返回：

```bash
tool list --limit 10
# 响应中包含 provider 提供的分页信息，如 "cursor": "abc123" 或 "offset": 10

tool list --cursor abc123 --limit 10    # cursor 风格
tool list --limit 10 --offset 10        # offset 风格
```

自建 API 层（不包装现有服务）时，opaque cursor 是更鲁棒的选择，因为 offset 在数据变动时不可靠。

---

## 9. 约束声明式设计：把"怎么做"写进命令

### 9.1 工具不内置 AI，但要为 AI 的调用设计好接口

这个工具本身不做翻译、不做摘要、不做推理——这些是调用它的 agent 负责的事。工具的职责是：把数据取对、格式定好、约束写清，让 agent 能精准地读取信息，再自己决定如何处理。

典型分工：

```bash
# 工具负责：把论文摘要取出来，格式化好
mycli paper abstract \
  --paper-id "doi://10.1234/xxxx" \
  --source semantic_scholar \
  --output-format json

# Agent 负责：拿到摘要之后，自己决定翻译/摘要/分析
# Agent 可以把上面命令的输出 pipe 给自己的下一步推理
```

这样做的好处：工具行为完全确定，agent 的 AI 调用可以独立测试和替换，二者解耦。

### 9.2 数据源可指定

任何涉及外部数据的命令都应支持 `--source` 参数，让 agent 自己决定去哪查，不在工具内部做"智能路由"：

```bash
mycli paper info --paper-id "doi://10.1234/xxxx" --source arxiv
mycli paper info --paper-id "doi://10.1234/xxxx" --source semantic_scholar
mycli paper info --paper-id "doi://10.1234/xxxx" --source local
```

多源并查时结果合并策略也必须显式声明：

```bash
mycli paper info --paper-id "doi://10.1234/xxxx" \
  --source arxiv,semantic_scholar \
  --merge-strategy first-wins   # first-wins | union | intersection
```

### 9.3 副作用必须显式声明

如果命令会写入数据、修改状态或发起网络请求，必须通过参数名或文档明确标注：

```bash
# 只读操作
mycli paper info --paper-id "doi://10.1234/xxxx"

# 写入操作，名称体现副作用
mycli paper add --paper-ref doi://10.1234/xxxx
mycli paper delete --paper-id "doi://10.1234/xxxx" --confirm

# 网络隔离
mycli paper info --paper-id "doi://10.1234/xxxx" --no-network
```

### 9.4 配置优先级

配置值的解析遵循以下优先级（高到低）：

```
flags > 环境变量 > 项目级配置 > 用户级配置 > 系统级配置
```

- 项目级配置：`./<cmd>.toml` 或 `./<cmd>/config.toml`
- 用户级配置：遵循 XDG Base Directory 规范，`$XDG_CONFIG_HOME/<cmd>/config.toml`
- 系统级配置：`/etc/<cmd>/config.toml`

每一层配置的来源应可通过 `--show-config-sources` 查看，便于 agent 调试配置冲突。

---

## 10. 版本与兼容：agent 工作流不能因升级而断

### 10.1 语义化版本

遵循 semver。对于 AI-Native CLI，breaking change 的定义包括：

- 输出 schema 字段删除或类型变更
- 退出码含义变更
- 参数名或枚举值的删除/重命名
- 默认行为变更

### 10.2 Schema 版本化

所有输出 schema 带版本号，agent 可以 pin 住特定版本：

```bash
mycli paper info --paper-id "..." --schema-version paper_info_v1
```

当 schema 升级时，旧版本继续支持至少一个主版本周期。

### 10.3 变更日志机器可读

```bash
mycli changelog --from v0.2.0 --to v0.3.0 --output-format json
```

返回 breaking changes、新增命令、废弃命令等结构化信息。

---

## 11. 安全与防呆：不信任调用方

### 11.1 必填参数必须校验

不设"智能默认值"。如果参数是必填的，缺失时直接报 `E_PARAM_REQUIRED`，退出码 2。

### 11.2 枚举值严格校验

如果 `--source` 只接受 `arxiv|semantic_scholar|local`，那么传入 `google` 应直接报错：

```json
{
  "error_code": "E_PARAM_INVALID_ENUM",
  "message": "--source value 'google' is not valid",
  "expected_values": ["arxiv", "semantic_scholar", "local"]
}
```

### 11.3 未知参数报错

不要静默忽略未知参数。`--papre-id`（拼写错误）应当直接报错而不是被忽略。

### 11.4 危险操作需确认

```bash
# 删除需要显式确认
mycli paper delete --paper-id "..." --confirm
# 没有 --confirm 则报错并提示

# 批量操作需要 --i-know-what-i-am-doing 或类似 flag
mycli library reset --confirm-destructive
```

### 11.5 密钥与凭证处理

正常使用优先 env / config，不靠 flag。推荐方式：

- 配置文件（权限 `0600`）
- stdin 管道：`cat token.txt | mycli auth login --token-stdin`
- 环境变量（备选）
- `--api-key` 等 token flag 可用于明确的一次性测试（不应作为持久凭证方式，因为会泄露到进程列表和 shell history）

---

## 12. 可观测性：让 agent 知道发生了什么

### 12.1 日志结构化

```bash
mycli paper add ... --verbose --log-format jsonl 2>run.log
```

日志每行是一条 JSON：

```json
{"ts":"2026-03-10T12:00:01Z","level":"info","msg":"Fetching from arxiv","paper_id":"2301.00001","latency_ms":230}
{"ts":"2026-03-10T12:00:02Z","level":"warn","msg":"Rate limited by semantic_scholar","retry_after_seconds":5}
```

### 12.2 进度信息输出到 stderr

长时间运行的命令应在 stderr 输出进度：

```bash
mycli paper add --input bulk.jsonl --input-format jsonl --verbose 2>&1 >/dev/null
# stderr: {"ts":"...","level":"info","msg":"Processing","current":42,"total":100}
```

Agent 可以选择忽略（`2>/dev/null`）或消费进度信息。

---

## 13. 信号处理与生命周期

- **Ctrl-C（SIGINT）**：立即停止当前操作，执行有界清理（最多 2 秒），然后退出。第二次 Ctrl-C 强制立即退出。
- **SIGTERM**：与 SIGINT 行为一致，优雅退出。
- **设计为 crash-only**：进程随时可被杀死，下次启动时自动恢复一致状态。不依赖"优雅关闭"来保证数据完整性。
- 长时间运行的操作应支持 `--timeout-seconds`，超时后以退出码 4 退出。

---

## 14. 发行与分发

- **单二进制优先**：尽可能编译为单个可执行文件，减少运行时依赖。
- **原生包管理**：提供 Homebrew、apt、scoop 等主流包管理器的安装方式。
- **卸载简单**：提供明确的卸载说明，清理配置和缓存目录。
- **版本自查**：`mycli --version` 输出版本号、构建时间、commit hash，便于 agent 确认运行环境。

---

## 15. 设计检查清单

为每个新命令上线前，检查以下清单：

```
□ 所有参数都用长名，没有短名快捷方式
□ 参数名自描述，无缩写
□ 输入类型用 URI scheme 编码（doi://、arxiv://），不靠推断
□ 支持 --input-format 和 --output-format
□ 默认输出是 json，不是 text
□ 输出包含 schema_version 和 timestamp
□ 退出码覆盖：成功/参数错误/数据不存在/上游失败/部分成功
□ 支持 stdin（--input -）和 stdout
□ stderr 仅输出错误和日志
□ 支持 --quiet / --verbose / --log-format
□ 支持 --no-network / --timeout-seconds / --max-items
□ 支持 --strict 模式
□ 支持 --dry-run（如有副作用）
□ 错误返回包含 error_code + message + fix_hint
□ 枚举值严格校验，未知参数报错
□ 幂等性：相同输入不产生重复副作用
□ --help 支持所有命令；--help --full 提供 examples + output schema + error codes
□ schema 可通过命令查看
□ 响应包含 next_actions 建议
□ 无"智能"行为——无语义搜索、无自动推断、无模糊排序
```

---

## 16. 反模式清单：AI-Native CLI 绝不做的事

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 短参数作为默认 | Agent 容易混淆 -p/-P/-d | 仅使用长参数名 |
| 自动推断输入类型 | 行为不可预测 | 用 URI scheme（doi://、arxiv://）自描述 |
| 语义搜索/模糊匹配 | 结果不可复现 | 用 contains/regex/exact |
| 交互式 prompt | Agent 无法自动化 | 所有输入通过参数传递 |
| 彩色/emoji 输出到 stdout | 破坏管道解析 | 仅在 stderr 且 --color=auto |
| 隐式默认值改变行为 | 升级后工作流静默失败 | 必填参数强制声明 |
| 输出格式不固定 | Agent 解析逻辑频繁失效 | Schema 版本化 |
| 静默忽略未知参数 | 拼写错误不被发现 | 未知参数直接报错 |
| "智能排序"等模糊词 | 不可解释、不可调试 | 明确声明排序算法 |
| 文档只有一个大 README | 上下文窗口浪费 | 分层文档 + CLI 内建查询 |
| 错误信息只有字符串 | Agent 无法程序化处理 | 结构化错误 + 错误码 |
| 把日志混入 stdout | 污染管道数据 | 日志只走 stderr |

---

## 17. 总结：AI-Native CLI 的十条铁律

1. **显式优于隐式**：所有约束写进参数，不靠推断和默认。
2. **结构化优于文本**：默认输出 JSON，text 是可选视图。
3. **确定性优于智能**：grep 优于语义搜索，BM25 优于"相关度"。
4. **长名优于短名**：`--paper-id` 而不是 `-p`。
5. **管道优于交互**：stdin/stdout/stderr 各司其职。
6. **可查询优于堆砌**：`--help --full` 提供完整文档，`--help --full --json` 机器可读。
7. **富信息优于精简**：每次响应带 summary + details + next_actions + refs。
8. **严格优于宽容**：未知参数报错，枚举值校验，`--strict` 模式。
9. **版本化优于自由演进**：Schema 带版本号，退出码不复用。
10. **可观测优于黑箱**：结构化日志、上游状态透明、进度可消费。
