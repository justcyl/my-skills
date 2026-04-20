# AI-Native CLI 设计检查清单

> 每个命令上线前逐项验证。全部通过方可发布。

---

## Must-Have Checks

| # | 检查项 | 通过 |
|---|--------|------|
| 1 | 默认输出格式为 JSON（`--json` 全局开关，或 `--output-format json`） | □ |
| 2 | 所有响应使用统一信封（schema_version / command / timestamp / result / errors / metadata） | □ |
| 3 | 响应包含 `schema_version` 字段，格式为 `<cmd>_<action>_v<n>` | □ |
| 4 | 所有参数使用长名（`--paper-id`），无默认短名 | □ |
| 5 | 参数名自描述，无缩写（`--output-format` 而非 `--fmt`） | □ |
| 6 | 错误输出结构化：`error_code` + `message` + `fix_hint` | □ |
| 7 | 退出码语义明确：0=成功 / 2=参数错误 / 3=不存在 / 4=上游失败 / 5=部分成功 | □ |
| 8 | 搜索使用确定性匹配（exact / contains / regex），无语义搜索 | □ |
| 9 | 分页使用 provider 实际提供的分页方式（cursor / next_url / offset / page_count） | □ |
| 10 | 每个命令支持 `--help`；至少一个命令支持 `--help --full`，输出 examples + output schema + error codes | □ |
| 11 | `--help --full` 支持 `--json` 输出机器可读结构（供 agent 解析） | □ |
| 12 | 提供 `--human` flag 切换人类友好模式 | □ |
| 13 | stdout 仅输出数据，stderr 仅输出日志/错误 | □ |
| 14 | 支持 stdin 输入（`--input -`） | □ |
| 15 | 枚举参数严格校验，非法值报 `E_PARAM_INVALID_ENUM` | □ |
| 16 | 未知参数报错，不静默忽略 | □ |
| 17 | 有副作用的命令支持 `--dry-run` | □ |
| 18 | 响应包含 `next_actions` 后续命令建议 | □ |
| 19 | 密钥不通过 flags 传递，使用文件/stdin/配置 | □ |
| 20 | 配置优先级正确：flags > env > project > user > system | □ |

---

## Anti-Pattern Checks

| # | 反模式 | 未违反 |
|---|--------|--------|
| 1 | 短参数作为默认（`-p` 代替 `--paper-id`） | □ |
| 2 | 非结构化错误输出（纯文本错误信息） | □ |
| 3 | 交互式 prompt（readline / 确认对话框） | □ |
| 4 | 语义搜索 / 模糊匹配作为默认搜索方式 | □ |
| 5 | offset/page 分页代替 cursor 分页（包装外部 API 时允许透传 provider 原生分页） | □ |
| 6 | 无版本号的 schema（输出缺少 `schema_version`） | □ |
| 7 | 自动推断输入类型（猜 DOI vs URL vs 标题） | □ |
| 8 | 日志/诊断信息混入 stdout | □ |
| 9 | 静默忽略未知参数 | □ |
| 10 | "智能排序" / "相关度"等不可解释的排序方式 | □ |
| 11 | 彩色/emoji 输出到 stdout（破坏管道解析） | □ |
| 12 | 密钥通过命令行 flags 传递（正常使用不应依赖 flag；`--api-key` 可用于明确的一次性测试） | □ |
