---
name: axonhub
description: 查询 AxonHub AI Gateway 的请求记录、Trace、UsageLog，以及管理渠道、API Key、模型等资源。使用官方 @axonhub/graphql-cli 工具通过 GraphQL API 操作，支持按 traceID、model、时间、状态筛选请求，也可探索 schema、执行任意 mutation。当用户需要查看 AxonHub 请求详情、排查 LLM 调用、查看 token 消耗、追踪 Trace、或通过命令行管理渠道/Key 时使用。
---

# AxonHub CLI

通过官方 `@axonhub/graphql-cli` 工具操作 AxonHub GraphQL API。无需安装，直接 `npx` 使用。

> **官方 skill 来源**：`looplj/axonhub` 仓库 `skills/axonhub-cli/SKILL.md`（PR #1149，v0.9.x+）

## 前置条件

- Node.js（支持 npx）
- `curl` 和 `jq`
- AxonHub 实例运行中（默认 `http://localhost:8090`）

```bash
# 验证工具可用
npx @axonhub/graphql-cli --version
```

---

## 第一步：认证登录

```bash
export AXONHUB_EMAIL="your-email@example.com"
export AXONHUB_PASSWORD="your-password"
AXONHUB_URL="http://localhost:8090"

AXONHUB_TOKEN=$(curl -s -X POST "${AXONHUB_URL}/admin/auth/signin" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${AXONHUB_EMAIL}\",\"password\":\"${AXONHUB_PASSWORD}\"}" \
  | jq -r '.token')

# 验证
[ "$AXONHUB_TOKEN" != "null" ] && [ -n "$AXONHUB_TOKEN" ] \
  && echo "✅ 登录成功" || echo "❌ 登录失败"
```

Token 有效期 7 天，过期后重新执行上面的命令即可。

---

## 第二步：注册 Endpoint

**只需配置一次**，之后所有查询用 `-e axonhub` 引用：

```bash
npx @axonhub/graphql-cli add axonhub \
  --url "${AXONHUB_URL}/admin/graphql" \
  --description "AxonHub GraphQL API"

npx @axonhub/graphql-cli login axonhub \
  --type token \
  --token "${AXONHUB_TOKEN}"

# 验证
npx @axonhub/graphql-cli list --detail
```

---

## 探索 Schema

不确定字段名时，先用 `find` 探索再查询，避免硬猜字段：

```bash
# 列出所有可用 query
npx @axonhub/graphql-cli find -e axonhub --query

# 列出所有可用 mutation
npx @axonhub/graphql-cli find -e axonhub --mutation

# 按关键词搜索（只显示名字）
npx @axonhub/graphql-cli find request -e axonhub
npx @axonhub/graphql-cli find channel -e axonhub

# 加 --detail 看完整字段定义
npx @axonhub/graphql-cli find request -e axonhub --detail

# 查 mutation 所需 input 类型
npx @axonhub/graphql-cli find CreateChannel -e axonhub --input --detail
```

> **规则**：先不加 `--detail` 看名字概览，确认是目标后再加 `--detail` 看完整定义，避免输出过多。

---

## 查询请求记录

### 最近 N 条请求

```bash
npx @axonhub/graphql-cli query \
  '{ requests(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      edges { node { id modelID status stream createdAt metricsLatencyMs metricsFirstTokenLatencyMs } }
    } }' \
  -e axonhub | jq '.requests'
```

### 按 Trace ID 查（一次用户消息触发的所有 LLM 子请求）

```bash
TRACE_ID="at-demo-123"

npx @axonhub/graphql-cli query \
  "{ requests(where: {traceID: \"$TRACE_ID\"}, orderBy: {field: CREATED_AT, direction: ASC}) {
      edges { node { id modelID status createdAt metricsLatencyMs } }
    } }" \
  -e axonhub | jq '.requests.edges[].node'
```

### 查某条请求的完整请求体/响应体

```bash
REQUEST_ID="12345"

npx @axonhub/graphql-cli query \
  "{ requests(where: {id: \"$REQUEST_ID\"}) {
      edges { node { id modelID status requestBody responseBody metricsLatencyMs } }
    } }" \
  -e axonhub | jq '.requests.edges[0].node'
```

> 若 `requestBody` / `responseBody` 为 null（内容已外存），改用 REST：
> ```bash
> curl -s "${AXONHUB_URL}/admin/requests/${REQUEST_ID}/content" \
>   -H "Authorization: Bearer ${AXONHUB_TOKEN}"
> ```

### 按模型名过滤

```bash
npx @axonhub/graphql-cli query \
  '{ requests(first: 20, where: {modelIDContainsFold: "claude"},
      orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      edges { node { id modelID status createdAt metricsLatencyMs } }
    } }' \
  -e axonhub | jq '.requests'
```

### 只看失败请求

```bash
npx @axonhub/graphql-cli query \
  '{ requests(first: 20, where: {status: failed},
      orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      edges { node { id modelID status createdAt } }
    } }' \
  -e axonhub | jq '.requests'
```

状态枚举：`pending` | `processing` | `completed` | `failed` | `canceled`

### 按时间范围过滤

```bash
npx @axonhub/graphql-cli query \
  '{ requests(first: 50,
      where: {createdAtGTE: "2025-04-25T00:00:00Z", createdAtLT: "2025-04-26T00:00:00Z"},
      orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      edges { node { id modelID status createdAt metricsLatencyMs } }
    } }' \
  -e axonhub | jq '.requests'
```

### 组合条件（and/or）

```bash
npx @axonhub/graphql-cli query \
  '{ requests(first: 20,
      where: { and: [
        { status: failed },
        { modelIDContainsFold: "gpt" },
        { createdAtGTE: "2025-04-26T10:00:00Z" }
      ]},
      orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      edges { node { id modelID status createdAt } }
    } }' \
  -e axonhub | jq '.requests'
```

---

## 查询 Token 用量（UsageLog）

```bash
npx @axonhub/graphql-cli query \
  '{ usageLogs(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
      edges { node { id modelID promptTokens completionTokens totalTokens totalCost createdAt } }
    } }' \
  -e axonhub | jq '.usageLogs.edges[].node'
```

---

## 查询 Trace

```bash
npx @axonhub/graphql-cli query \
  '{ traces(first: 10, orderBy: {field: CREATED_AT, direction: DESC}) {
      edges { node { id traceID createdAt
        requests { edges { node { id modelID status metricsLatencyMs } } }
      } }
    } }' \
  -e axonhub | jq '.traces.edges[].node'
```

---

## 管理资源（常用 Query/Mutation）

### 查看系统状态

```bash
npx @axonhub/graphql-cli query \
  '{ systemStatus { isInitialized }
     systemVersion { version commit uptime } }' \
  -e axonhub | jq '.'
```

### 查看渠道列表

```bash
npx @axonhub/graphql-cli query \
  '{ queryChannels(input: { first: 20 }) {
      edges { node { id name type status supportedModels } }
    } }' \
  -e axonhub | jq '.queryChannels.edges[].node'
```

### 测试渠道连通性

```bash
CHANNEL_ID="1"
npx @axonhub/graphql-cli mutate \
  "mutation { testChannel(input: { channelID: \"$CHANNEL_ID\" }) {
      success latency message error
    } }" \
  -e axonhub | jq '.testChannel'
```

### 启用/禁用渠道

```bash
npx @axonhub/graphql-cli mutate \
  'mutation { updateChannelStatus(id: "1", status: enabled) { id name status } }' \
  -e axonhub
```

### 当前登录用户信息

```bash
npx @axonhub/graphql-cli query \
  '{ me { id email firstName lastName isOwner scopes } }' \
  -e axonhub | jq '.me'
```

---

## 分页

```bash
# 第一页，同时取 pageInfo
npx @axonhub/graphql-cli query \
  '{ requests(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      totalCount
      edges { node { id modelID createdAt } }
    } }' \
  -e axonhub | jq '.'

# 翻下一页（把 endCursor 填入 after）
npx @axonhub/graphql-cli query \
  '{ requests(first: 20, after: "<endCursor>",
      orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      edges { node { id modelID createdAt } }
    } }' \
  -e axonhub | jq '.'
```

---

## Request 字段速查

| 字段 | 说明 |
|------|------|
| `id` | 请求 ID |
| `modelID` | 模型名 |
| `status` | `pending/processing/completed/failed/canceled` |
| `stream` | 是否流式 |
| `source` | `api/playground/test` |
| `requestBody` | 请求体（可能 null，已外存时用 REST 下载）|
| `responseBody` | 响应体（同上）|
| `metricsLatencyMs` | 总延迟（ms）|
| `metricsFirstTokenLatencyMs` | 首 token 延迟（ms）|
| `metricsReasoningDurationMs` | 推理时长（ms）|
| `traceID` | 所属 Trace（外键 ID）|
| `channelID` | 路由到的渠道 ID |
| `createdAt` | 请求时间 |
