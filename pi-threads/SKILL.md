---
name: pi-threads
description: 搜索、定位和阅读历史 pi 会话记录。当需要查找之前做得好的对话、提取 pattern 转化为 skill、或回顾过去的决策时使用。
---

# pi-threads

搜索和阅读历史 pi coding agent 会话的 CLI 工具。将 `~/.pi/agent/sessions/` 中的 JSONL 会话文件索引到本地 SQLite FTS5 数据库，提供快速搜索、模糊定位和清洁阅读。

## 前置检查

```bash
command -v pi-threads || echo "NOT INSTALLED — see /Users/chenyl/project/pi-threads/README.md"
```

## 第一步：确保索引是最新的

```bash
pi-threads --json sync
```

增量同步，只处理有变化的文件。首次约 1-2 秒。

## 核心工作流

### 1. 搜索消息

跨所有会话全文搜索：

```bash
pi-threads --json messages search "build a CLI" --limit 10
pi-threads --json messages search "pytest" --role user --project ph2
```

### 2. 模糊定位线程

当你知道大概内容但不知道 session ID 时：

```bash
pi-threads --json threads resolve "paper format check"
pi-threads --json threads resolve "skill creation"
```

### 3. 阅读线程

获取清洁的 user + assistant 消息（已移除 tool noise）：

```bash
pi-threads --json threads read <session-id-or-prefix>
```

支持部分 ID：`pi-threads --json threads read 69107ac3`

### 4. 查看原始事件

需要完整上下文（包括 tool 调用和结果）时：

```bash
pi-threads --json events read <session-id> --limit 50
```

### 5. 列出线程

```bash
pi-threads --json threads list --limit 10
pi-threads --json threads list --project sttrl
```

## 典型场景：从线程提取 skill

```bash
# 1. 搜索关键词找到相关线程
pi-threads --json messages search "overleaf review" --limit 5

# 2. 阅读找到的线程
pi-threads --json threads read <session-id>

# 3. 从对话中提取 pattern，写成 skill
```

## 输出格式

所有 `--json` 输出使用标准信封，包含 `result`、`metadata`、`next_actions`。

## 注意

- 首次使用前需要 `pi-threads --json sync`
- 搜索默认使用 FTS5 全文检索，也支持 `--match-mode contains` 和 `--match-mode exact`
- 不需要网络，纯本地操作
