# AI-Native CLI 规范模板

> 使用本模板为每个 AI-Native CLI 生成完整的接口规范。
> 填写所有章节，删除不适用的部分并注明原因。

---

## 1. Meta

| 字段 | 值 |
|------|-----|
| 命令名 | `<cmd>` |
| 一句话用途 | |
| 主要消费者 | agent / human / both |
| schema_version | `<cmd>_spec_v1` |
| 运行时/语言 | |
| 平台 | macOS / Linux / Windows |
| 分发方式 | 单二进制 / 包管理器 / 容器 |

---

## 2. Command Tree

```
<cmd> <resource> <action> [flags]
```

### Subcommands

| 子命令 | 用途 | 幂等 | 副作用 |
|--------|------|------|--------|
| `<cmd> <resource> list` | | ✓ | 只读 |
| `<cmd> <resource> info` | | ✓ | 只读 |
| `<cmd> <resource> add` | | ✓ | 写入 |
| `<cmd> <resource> delete` | | ✗ | 写入 |
| `<cmd> <resource> search` | | ✓ | 只读 |

---

## 3. Global Flags

| Flag | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--help` | bool | false | 输出帮助信息（支持 `--output-format json`） |
| `--version` | bool | false | 输出版本号、构建时间、commit hash |
| `--human` | bool | false | 启用人类友好模式（短参数、彩色输出） |
| `--json` | bool | false | 输出 JSON（布尔开关，与 `--output-format json` 等效） |
| `--output-format` | enum | - | `jsonl` \| `tsv` \| `text`（需要非 JSON 格式时使用） |
| `--input` | string | - | 输入文件路径，`-` 表示 stdin |
| `--input-format` | enum | jsonl | `json` \| `jsonl` \| `tsv` \| `plain` |
| `--config` | path | - | 指定配置文件路径 |
| `--log-level` | enum | warn | `debug` \| `info` \| `warn` \| `error` |
| `--log-format` | enum | text | `jsonl` \| `text` |
| `--quiet` | bool | false | 抑制所有 stderr 输出 |
| `--verbose` | bool | false | 输出详细日志到 stderr |
| `--no-network` | bool | false | 仅查本地数据 |
| `--timeout-seconds` | int | 30 | 操作超时秒数 |
| `--max-items` | int | 100 | 限制输出条数 |
| `--strict` | bool | false | 任何非致命错误以非 0 退出 |
| `--dry-run` | bool | false | 预检操作效果，不执行副作用 |
| `--show-config-sources` | bool | false | 显示配置值来源 |

---

## 4. Per-Subcommand Flags

### `<cmd> <resource> <action>`

| Flag | 类型 | 必填 | 默认值 | URI Scheme | 说明 |
|------|------|------|--------|------------|------|
| `--<resource>-ref` | uri | ✓ | - | `doi://`, `arxiv://`, ... | 资源引用 |
| `--source` | enum | ✗ | local | `arxiv` \| `local` \| ... | 数据源 |
| `--merge-strategy` | enum | ✗ | first-wins | `first-wins` \| `union` | 多源合并策略 |

> 为每个子命令复制此表并填写。

---

## 5. Response Envelope

所有命令的 JSON 输出遵循统一信封格式：

```json
{
  "schema_version": "<cmd>_<action>_v1",
  "command": "<resource> <action>",
  "timestamp": "2026-03-10T12:00:00Z",
  "summary": "...",
  "result": [],
  "errors": [],
  "metadata": {
    "total_count": 0,
    "returned_count": 0,
    "has_more": false,
    "cursor": null
  },
  "next_actions": [],
  "refs": []
}
```

---

## 6. Result Schemas

### `<resource> <action>` → `<cmd>_<action>_v1`

```json
{
  "field_name": "type — 说明"
}
```

> 为每个子命令定义 result 数组中单个元素的 schema。

---

## 7. Error Codes

| error_code | 退出码 | message 模板 | fix_hint |
|------------|--------|-------------|----------|
| `E_PARAM_REQUIRED` | 2 | `--<param> is required` | 提供必填参数 |
| `E_PARAM_INVALID_ENUM` | 2 | `--<param> value '<val>' is not valid` | 列出合法值 |
| `E_UNKNOWN_PARAM` | 2 | `Unknown parameter '--<param>'` | 检查拼写 |
| `E_UNKNOWN_REF_SCHEME` | 2 | `Unsupported scheme '<s>' in --<param>` | 列出支持的 scheme |
| `E_NOT_FOUND` | 3 | `Resource not found` | 检查标识符 |
| `E_UPSTREAM_FAILURE` | 4 | `<source> returned error: <detail>` | 重试或换源 |
| `E_PARTIAL_SUCCESS` | 5 | `<n>/<total> items failed` | 查看 errors 数组 |

> 补充命令特有的错误码。

---

## 8. Exit Codes

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 通用运行时错误 |
| 2 | 参数错误（缺失/类型/枚举/未知） |
| 3 | 数据不存在 |
| 4 | 上游源失败 / 超时 |
| 5 | 部分成功（批量操作） |

---

## 9. Search / Filter Contract

### Match Modes

| `--match-mode` | 行为 |
|----------------|------|
| `exact` | 精确匹配 |
| `contains` | 子串包含（大小写不敏感） |
| `regex` | 正则表达式 |

### 可搜索字段

| `--field` | 说明 |
|-----------|------|
| | |

### 排序

| `--sort-by` | 说明 |
|-------------|------|
| | |

### Cursor 分页

```bash
<cmd> <resource> list --max-items 10
# 响应 metadata.cursor = "abc123"

<cmd> <resource> list --cursor abc123 --max-items 10
```

---

## 10. `--help --full` 覆盖范围

每个命令必须支持标准 `--help`，同时实现 `--help --full` 提供完整文档：

```bash
<cmd> <resource> <action> --help       # 标准：synopsis + flags
<cmd> <resource> <action> --help --full  # 完整：synopsis + flags + examples + output schema + error codes
<cmd> <resource> <action> --help --full --json  # 机器可读版本
```

`--help --full` 输出结构：

```
COMMAND
  <resource> <action> — <一句话描述>

USAGE
  <cmd> --json <resource> <action> --<required-flag> <value> [flags]

FLAGS
  --<flag>   <type>  <default/required>  <说明>
  ...

OUTPUT SCHEMA
  { "field": "type — 说明" }

ERROR CODES
  <ERROR_CODE>  exit <n>  <触发条件>  Run: <修复命令>

EXAMPLES
  # 示例描述
  <cmd> --json <resource> <action> --<flag> <value>

  # 管道用法
  <cmd> --json <resource> <action> ... | jq '...'
```

`--help --full --json` 输出示例：

```json
{
  "command": "<resource> <action>",
  "synopsis": "...",
  "flags": [
    { "name": "--<flag>", "type": "string", "required": true, "description": "..." }
  ],
  "output_schema": { "field": "type" },
  "error_codes": [
    { "code": "E_...", "exit": 1, "description": "...", "fix": "<cmd> ..." }
  ],
  "examples": [
    { "description": "...", "command": "<cmd> --json ..." }
  ]
}
```

---

## 11. Config / Env 优先级

```
flags > 环境变量 > 项目级配置 > 用户级配置 > 系统级配置
```

| 层级 | 路径 |
|------|------|
| 项目级 | `./<cmd>.toml` |
| 用户级 | `$XDG_CONFIG_HOME/<cmd>/config.toml` |
| 系统级 | `/etc/<cmd>/config.toml` |

环境变量命名：`<CMD>_<PARAM>`（大写 + 下划线）。

---

## 12. Secrets 处理

| 方式 | 推荐度 | 说明 |
|------|--------|------|
| 配置文件（0600） | 推荐 | 持久化凭证 |
| stdin 管道 | 推荐 | `cat token \| <cmd> auth --token-stdin` |
| 环境变量 | 备选 | 不推荐长期使用 |
| 命令行 flags | 禁止 | 泄露到进程列表和 shell 历史 |

---

## 13. Signal Handling

| 信号 | 行为 |
|------|------|
| SIGINT (Ctrl-C) | 停止当前操作，有界清理（≤2s），退出 |
| SIGINT ×2 | 强制立即退出 |
| SIGTERM | 同 SIGINT，优雅退出 |

设计为 crash-only：进程随时可被杀死，下次启动自动恢复一致状态。

---

## 14. Examples

> 提供 5-10 个示例，覆盖：正常用法、JSON 输出、错误场景、管道组合、批量操作。

```bash
# 1. 基本查询
<cmd> <resource> info --<resource>-ref doi://10.1234/xxxx

# 2. JSON 输出 + jq 管道
<cmd> <resource> list --output-format json | jq '.result[].title'

# 3. 批量输入
cat input.jsonl | <cmd> <resource> add --input - --input-format jsonl

# 4. 错误场景
<cmd> <resource> info --<resource>-ref invalid://xxx
# 退出码 2, error_code: E_UNKNOWN_REF_SCHEME

# 5. 搜索 + 过滤
<cmd> <resource> search --query "keyword" --field title --match-mode contains --max-items 5

# 6. 分页
<cmd> <resource> list --max-items 10
<cmd> <resource> list --cursor <cursor> --max-items 10

# 7. Dry-run
<cmd> <resource> delete --<resource>-id "..." --dry-run

# 8. 人类模式
<cmd> <resource> list --human
```

---

## 15. Schema Changelog

| 版本 | 日期 | 变更 |
|------|------|------|
| `<cmd>_spec_v1` | YYYY-MM-DD | 初始版本 |
