---
name: ai-native-cli
description: 设计 AI-Native CLI 接口规范——agent-first, human-compatible。命令树、参数、响应信封、错误码、分页、文档分层，全部为 agent 消费优化。
---

# AI-Native CLI

设计 agent-first 的 CLI 接口规范：结构化输出、确定性行为、可组合管道。

## Do This First

- 加载 `references/ai-native-principles.md` 作为设计准则。
- 本 skill 专注 agent-first CLI 设计。如果用户需要 human-first、script-friendly 的传统 CLI，告知其不在本 skill 范围内。

## Clarify (fast)

逐项确认，用户不确定时用 agent-first 默认值：

1. **命令名 + 一句话用途**：这个 CLI 做什么？
2. **主要消费者**：哪类 agent 会调用？需要兼顾人类访问吗？
3. **输入类型**：是否需要 URI scheme 自描述输入（`doi://`、`arxiv://`）？有哪些 scheme？
4. **数据领域**：操作什么实体/资源？需要搜索和过滤吗？
5. **上游依赖**：外部 API、数据库、限流约束？
6. **输出契约**：result 里放什么字段？需要分页吗？
7. **配置模型**：flags / env / config-file 哪些需要？
8. **平台/运行时**：目标 OS、语言/运行时、分发方式？

## Deliverables

使用 `references/spec-template.md` 模板输出完整规范，必须包含以下章节：

1. Meta（命令名、用途、消费者、平台、分发）
2. Command Tree + Subcommands 表
3. Global Flags 表
4. Per-Subcommand Flags 表（含 URI Scheme 列）
5. Response Envelope JSON schema
6. Result Schemas（每个子命令）
7. Error Codes 表（error_code + 退出码 + message + fix_hint）
8. Exit Codes 表
9. Search/Filter Contract（match modes、cursor 分页）
10. Documentation Layers（L0-L3）
11. Config/Env 优先级表
12. Secrets 处理
13. Signal Handling
14. Examples（5-10 个，含 JSON 输出、错误场景、管道用法）
15. Schema Changelog

## Default Conventions

除非用户明确覆盖，采用以下默认值：

### Agent-First 默认值
- 默认输出 JSON，`--human` 切换人类模式
- 所有参数使用长名，无默认短名
- 响应使用统一信封（schema_version / command / timestamp / result / errors / metadata / next_actions）
- 错误结构化：error_code + message + fix_hint
- 搜索使用确定性匹配（exact / contains / regex）
- 分页使用 opaque cursor
- 文档分层（L0-L3），help 输出支持 JSON
- 退出码语义化（0-5）
- 幂等设计，`--dry-run` 预检副作用

### 通用工程实践
- 配置优先级：flags > env > project config > user config > system config
- XDG Base Directory 规范存放用户配置
- 信号处理：Ctrl-C 快速退出、有界清理（≤2s）、crash-only 设计
- 密钥处理：never via flags，prefer file/stdin
- 发行：单二进制优先，提供主流包管理器安装

## Verify

规范完成后，用 `references/design-checklist.md` 逐项验证：
- 20 项 Must-Have Checks 全部通过
- 12 项 Anti-Pattern Checks 全部未违反

将验证结果附在规范末尾。

## Notes

- 本 skill 语言无关，不推荐特定实现语言或框架。
- 本 skill 不覆盖 human-first CLI 设计场景。
- 本 skill 只设计接口规范，不生成实现代码。如需实现，用户应将规范交给编码 agent。
