---
name: ai-native-cli
description: 从零到可用的 Agent-Native CLI：设计 agent-first 接口规范，从 API 文档/OpenAPI/curl 示例/SDK 构建可安装二进制，最后生成 companion skill。覆盖纯规范设计和完整实现两种场景。
---

# AI-Native CLI Creator

从源材料到可安装 CLI，再到 companion skill 的完整工作流，分三个阶段：

1. **Spec**：设计 agent-first 接口规范（命令树、响应信封、错误码、文档分层）
2. **Build**：选择运行时，脚手架、实现、安装、测试
3. **Companion**：生成伴侣 skill，让未来的 agent 知道如何使用这个工具

只需要规范设计（不写代码）时，Phase 2 和 Phase 3 可以跳过。

## Do This First

- 加载 `references/ai-native-principles.md` 作为设计准则。
- 明确用户意图：纯规范设计 → Phase 1 only；有源材料要构建工具 → Phase 1 + 2 + 3。

## Start（有源材料时）

明确三件事再开始：

- **Source**：API 文档、OpenAPI JSON、SDK 文档、curl 示例、浏览器 app DevTools、现有内部脚本，或已有的 shell history。
- **Jobs**：具体的读写任务，如 `list drafts`、`download failed job logs`、`search messages`、`upload media`。
- **Install name**：简短的二进制名称，如 `ci-logs`、`slack-cli`、`sentry-cli`。

如果用户只需要一次性脚本，写脚本而不是建 CLI。CLI 是为**可重复调用的持久工具**设计的。

安装前先检查命令是否已存在：

```bash
command -v <tool-name> || true
```

若已存在，选择更清晰的名称或询问用户。

---

## Phase 1: Spec Design

### Clarify（fast）

逐项确认，用户不确定时用 agent-first 默认值：

1. **命令名 + 一句话用途**：这个 CLI 做什么？
2. **主要消费者**：哪类 agent 会调用？需要兼顾人类访问吗？
3. **源材料类型**：API docs / OpenAPI / SDK / curl 示例 / 无（纯设计）？
4. **输入类型**：是否需要 URI scheme 自描述输入（`doi://`、`arxiv://`）？有哪些 scheme？
5. **数据领域**：操作什么实体/资源？需要搜索和过滤吗？
6. **上游依赖**：外部 API、数据库、限流约束？认证方式？
7. **输出契约**：result 里放什么字段？需要分页吗？
8. **配置模型**：flags / env / config-file 哪些需要？
9. **平台/运行时偏好**：目标 OS、语言偏好、分发方式？（Phase 2 使用）

### Command Surface Sketch

在写代码或完整规范前，先在 chat 中勾画命令面。命令面设计参考 `references/agent-cli-patterns.md`，应回答：

- 能发现哪些容器（accounts / projects / workspaces）？
- 能精确读取哪些对象？
- 能把名称/URL/slug 解析为稳定 ID 吗？
- 能下载或上传哪些文件？
- 有哪些写操作？
- Raw escape hatch 是什么？

### Deliverables（Spec）

使用 `references/spec-template.md` 模板输出完整规范，必须包含以下章节：

1. Meta（命令名、用途、消费者、平台、分发）
2. Command Tree + Subcommands 表
3. Global Flags 表
4. Per-Subcommand Flags 表（含 URI Scheme 列）
5. Response Envelope JSON schema
6. Result Schemas（每个子命令）
7. Error Codes 表（error_code + 退出码 + message + fix_hint）
8. Exit Codes 表
9. Search/Filter Contract（match modes）
10. `--help --full` 覆盖范围说明（examples、output schema、error codes 各命令至少覆盖）
11. Config/Env 优先级表
12. Secrets 处理
13. Signal Handling
14. Examples（5-10 个，含 JSON 输出、错误场景、管道用法）
15. Schema Changelog

**规范完成后，用 `references/design-checklist.md` 验证，20 项 Must-Have 全部通过、12 项 Anti-Pattern 全部未违反后，方可进入 Phase 2。**

---

## Phase 2: Build

_如果用户只需要规范，本阶段跳过，将规范交给编码 agent 实现。_

### Choose the Runtime

检查用户机器和源材料：

```bash
command -v cargo rustc node pnpm npm python3 uv || true
```

按以下优先级选择运行时：

- **Rust**：目标是持久化 CLI，agent 需要从任意 repo 调用，追求单二进制、快速启动、强类型 JSON。
- **TypeScript/Node**：官方 SDK、auth helper、浏览器自动化库，或现有 repo tooling 是 Node 生态时。
- **Python**：数据科学、本地文件变换、notebook、SQLite/CSV/JSON 分析，或 Python-heavy admin 工具。

选择前用一句话声明：选择的语言、原因、检测到的工具链。不要选择增加安装摩擦的语言，除非有实质性收益。若最佳语言未安装，获得用户同意后再安装，或选择次优已安装选项。

### Build Workflow

1. **Inventory**：读取源材料，盘点资源、认证、分页、ID 格式、媒体/文件流、限流、危险写操作。如果有 OpenAPI，优先下载检查再命名命令。
2. **Sketch**：在 chat 中勾画命令列表，保持名称简短、shell 友好，确认后再写代码。
3. **Scaffold**：创建项目结构 + README（含 JSON 策略文档：API 直传 vs CLI 信封、成功结构、错误结构、每个命令族的示例）。
4. **Implement**：先实现 `doctor`、discovery、resolve、read 命令；再实现 dry-run write；最后实现 raw escape hatch。
5. **Install**：将 CLI 安装到 PATH，使 `tool-name ...` 在 source folder 外也能工作。
6. **Smoke Test**：从另一个 repo 或 `/tmp` 测试，不只用 `cargo run` 或包管理器包装：
   ```bash
   command -v <tool-name>
   <tool-name> --help
   <tool-name> --json doctor
   ```
7. **Test**：格式化、类型检查/构建、request builder 单元测试、分页/请求体构建器测试、no-auth `doctor`、至少一个 fixture 或 dry-run 或只读 API 调用。

如需 live write 才能验证，先询问用户，确保操作可逆或为 draft-only。

**特殊场景：**

- **已有脚本/shell history**：拆成 setup → discovery → download → transform → draft → upload → poll → live write 阶段，保留用户已有的 flags、路径、环境变量，再用稳定 ID、有界 JSON 和文件输出包装可重复阶段。
- **媒体/presigned upload**：分阶段单独测试：创建 upload → 传输字节 → 轮询处理状态 → 挂载或引用结果 ID。
- **Log-oriented CLI**：把确定性片段提取（文件名、行号/字节范围、匹配规则、摘录）与模型解读严格分离，前者由 CLI 负责。
- **Fixture-backed 原型**：fixtures 放在项目可预测路径，从 `/tmp` smoke-test 确保安装后仍能找到。

### Auth and Config

优先级从高到低：

1. 服务标准名称的环境变量，如 `GITHUB_TOKEN`
2. 用户配置文件 `~/.<tool-name>/config.toml`（或其他简单文档化路径）
3. `--api-key` 或工具专用 token flag，用于明确的一次性测试；正常使用优先 env / config，因为 flag 可能泄露到进程列表和 shell history

绝不打印完整 token。`doctor --json` 必须报告：

- token 是否存在
- 认证来源类别（`flag` / `env` / `config` / provider default / missing）
- 缺少的设置步骤

CLI 在无网络/无认证下可运行时，`doctor --json` 应明确报告 fixture/offline 模式、是否找到 fixture 数据、该模式是否不需要认证。

**内部 web app 来源的 curl**：先提取 sanitized endpoint notes（资源名、method/path、必要 header、认证机制、CSRF 行为、请求体、响应 ID 字段、分页、错误、脱敏样例响应）再实现。不提交 cookie、bearer token、客户密钥或完整生产 payload。截图仅用于推断 UI 流程和字段，不作为 API 证据（需配合网络请求或 fixture）。

### Runtime Defaults

#### Rust

```toml
clap          # 命令解析和 help
reqwest       # HTTP
serde / serde_json  # payload
toml          # config
anyhow        # 错误上下文
```

提供 `Makefile` target `make install-local`：构建 release 并安装到 `~/.local/bin`。

#### TypeScript/Node

```
commander 或 cac    # 命令解析
native fetch / 官方 SDK / 已有 HTTP helper
zod                 # 仅当外部 payload 校验确实防止真实 breakage 时
package.json bin    # 安装命令
```

`pnpm install && pnpm build && pnpm link --global`，或 `make install-local` 在 `~/.local/bin` 安装小包装脚本。

#### Python

```python
argparse 或 typer        # 命令解析（子命令复杂时用 typer）
urllib / requests / httpx # HTTP（用已安装或已有的）
json, csv, sqlite3, pathlib, subprocess  # 本地操作
pyproject.toml console script
```

`make install-local`，文档说明是否依赖 `uv` / virtualenv / system Python。

---

## Phase 3: Companion Skill

CLI 工作后，为它创建一个 companion skill。

**skills-manager** 是统一管理 skill 仓库（`~/project/my-skills`）的 skill，负责 skill 的创建、注册、分发全流程。先阅读 skills-manager 的 SKILL.md，再将此任务交给它处理。

创建时提供以下上下文：

- **skill 名称**：`<tool-name>`
- **description**：一句话描述这个 CLI 做什么、主要消费者是谁
- **核心内容提示**（按 future agent 使用顺序）：
  1. 如何验证命令已安装
  2. 第一个要运行的命令（通常是 `--json doctor`）
  3. 认证如何配置（env var 名称、config 路径）
  4. 哪个 discovery 命令找到常用 ID
  5. 安全的只读路径
  6. 预期的 draft/write 路径
  7. Raw escape hatch
  8. 未经用户明确批准不能做什么
  9. 三个可直接复制的命令示例

API 参考细节放在 CLI README 里；companion skill 专注顺序、安全性和示例，保持精简。

---

## Default Conventions

### Agent-First 默认值

- 默认输出 JSON：`--json` 为全局布尔开关（仿 gh/kubectl 风格）；需要多格式（jsonl/tsv/text）时使用 `--output-format`；`--human` 切换人类模式
- 所有参数使用长名，无默认短名（`--json field1,field2` 字段选择输出除外，沿用 gh CLI 约定）
- 响应使用统一信封（schema_version / command / timestamp / result / errors / metadata / next_actions）
- 错误结构化：error_code + message + fix_hint
- 搜索使用确定性匹配（exact / contains / regex）
- 分页：返回 provider 实际提供的分页信息（`next_cursor`、`next_url`、`offset`、`page_count` 均可接受）
- `--help` 标准行为（synopsis + flags）；`--help --full` 扩展输出 examples + output schema + error codes；`--help --full --json` 机器可读版本
- 退出码语义化（0-5）
- 幂等设计，`--dry-run` 预检副作用

### 通用工程实践

- 配置优先级：flags > env > project config > user config > system config
- XDG Base Directory 规范存放用户配置
- 信号处理：Ctrl-C 快速退出、有界清理（≤2s）、crash-only 设计
- 密钥处理：正常使用优先 env / config；`--api-key` 等 token flag 可用于明确的一次性测试
- 发行：单二进制优先，提供主流包管理器安装

---

## Verify

规范完成后，用 `references/design-checklist.md` 逐项验证：

- 20 项 Must-Have Checks 全部通过
- 12 项 Anti-Pattern Checks 全部未违反

将验证结果附在规范末尾。

---

## Notes

- **Scope**：本 skill 语言无关用于 spec 设计；Phase 2 提供运行时选择指南，但不强制特定语言或框架。
- **分阶段使用**：Phase 1 可独立交付（规范），Phase 2 和 3 可由任何编码 agent 执行。
- **通用性**：本 skill 对所有编码 agent 通用，不绑定特定模型或平台。
- **Human-first CLI**：本 skill 以 agent-first 为优先设计目标；如需纯 human-first CLI 设计，告知用户此场景不在本 skill 范围内。
