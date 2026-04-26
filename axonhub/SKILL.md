---
name: axonhub
description: 查询 AxonHub AI Gateway 的请求记录、Trace、UsageLog。通过 GraphQL API 认证登录并检索请求体/响应体/延迟/token 用量，支持按 traceID、model、时间范围、状态筛选。当用户需要查看 AxonHub 某个请求详情、排查 LLM 调用、查看 token 消耗、或追踪特定 Trace 下的所有请求时使用。
---

# AxonHub 请求查询

AxonHub 是一个 AI Gateway，所有流经它的 LLM 请求都会被记录。本 skill 教你用 GraphQL API 查询这些记录，无需打开 Web UI。

## 本地配置

默认配置文件：`~/.config/axonhub/config.yml`

```bash
# 读取本地端口
grep "port:" ~/.config/axonhub/config.yml
# 通常是 8090
```

本 skill 中 `AXONHUB_BASE` 默认为 `http://localhost:8090`，如需修改请替换相应 URL。

---

## 第一步：获取认证 Token

AxonHub 管理 API 使用 JWT。每次查询前先登录拿 token：

```bash
AXONHUB_BASE="http://localhost:8090"

TOKEN=$(curl -s -X POST "$AXONHUB_BASE/admin/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }' | jq -r '.data.signIn.token')

echo "TOKEN=$TOKEN"
```

> 如果响应里没有 `.data.signIn.token`，用 `| jq '.'` 先看完整结构。

Token 获取后在后续所有请求中加 `-H "Authorization: Bearer $TOKEN"`。

---

## 查询方式

所有管理查询走 **GraphQL**：

- **Endpoint**：`POST /admin/graphql`
- **Auth**：`Authorization: Bearer <JWT_TOKEN>`
- **Playground（浏览器交互）**：`GET /admin/graphql/playground`

基础 curl 模板：

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ ... }"}' | jq '.'
```

---

## 常用查询

### 1. 最近 N 条请求

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ requests(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) { totalCount edges { node { id modelID status stream createdAt metricsLatencyMs metricsFirstTokenLatencyMs } } } }"
  }' | jq '.data.requests'
```

### 2. 按 Trace ID 查询（一个用户消息触发的所有 LLM 请求）

```bash
TRACE_ID="at-demo-123"

curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"{ requests(where: {traceID: \\\"$TRACE_ID\\\"}, orderBy: {field: CREATED_AT, direction: ASC}) { edges { node { id modelID status createdAt metricsLatencyMs } } } }\"
  }" | jq '.data.requests.edges[].node'
```

或者用 traces 查询（同时拿到 Trace 元信息）：

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"{ traces(where: {traceID: \\\"$TRACE_ID\\\"}) { edges { node { id traceID createdAt requests { edges { node { id modelID status metricsLatencyMs } } } } } } }\"
  }" | jq '.data.traces.edges[].node'
```

### 3. 查看某个请求的完整请求体 / 响应体

```bash
REQUEST_ID="12345"

curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"{ requests(where: {id: \\\"$REQUEST_ID\\\"}) { edges { node { id modelID status requestBody responseBody requestHeaders metricsLatencyMs metricsFirstTokenLatencyMs } } } }\"
  }" | jq '.data.requests.edges[0].node'
```

> **注意**：如果 `requestBody` / `responseBody` 返回 `null`，说明内容已被外存（contentSaved = true），用 REST 接口下载：
>
> ```bash
> curl -s "$AXONHUB_BASE/admin/requests/$REQUEST_ID/content" \
>   -H "Authorization: Bearer $TOKEN"
> ```

### 4. 按模型名过滤

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ requests(first: 20, where: {modelIDContainsFold: \"claude\"}, orderBy: {field: CREATED_AT, direction: DESC}) { totalCount edges { node { id modelID status createdAt metricsLatencyMs } } } }"
  }' | jq '.data.requests'
```

### 5. 按状态筛选（只看失败的请求）

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ requests(first: 20, where: {status: failed}, orderBy: {field: CREATED_AT, direction: DESC}) { totalCount edges { node { id modelID status createdAt } } } }"
  }' | jq '.data.requests'
```

状态枚举值：`pending` | `processing` | `completed` | `failed` | `canceled`

### 6. 按时间范围过滤

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ requests(first: 50, where: {createdAtGTE: \"2025-04-25T00:00:00Z\", createdAtLT: \"2025-04-26T00:00:00Z\"}, orderBy: {field: CREATED_AT, direction: DESC}) { totalCount edges { node { id modelID status createdAt metricsLatencyMs } } } }"
  }' | jq '.data.requests'
```

### 7. 查询 Token 用量（UsageLog）

```bash
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ usageLogs(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) { edges { node { id modelID promptTokens completionTokens totalTokens promptCachedTokens totalCost createdAt } } } }"
  }' | jq '.data.usageLogs.edges[].node'
```

按 requestID 关联 UsageLog：

```bash
REQUEST_ID="12345"
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"{ usageLogs(where: {requestID: \\\"$REQUEST_ID\\\"}) { edges { node { promptTokens completionTokens totalTokens totalCost } } } }\"
  }" | jq '.data.usageLogs.edges[0].node'
```

### 8. 组合条件过滤

`where` 支持 `and` / `or` / `not` 逻辑组合：

```graphql
# 最近 1 小时内、失败的、使用 gpt 系列模型的请求
{
  requests(
    first: 20
    where: {
      and: [
        { status: failed }
        { modelIDContainsFold: "gpt" }
        { createdAtGTE: "2025-04-26T10:00:00Z" }
      ]
    }
    orderBy: { field: CREATED_AT, direction: DESC }
  ) {
    totalCount
    edges {
      node { id modelID status createdAt }
    }
  }
}
```

---

## 分页

所有列表查询都支持 cursor-based 分页：

```bash
# 获取第一页（同时取 pageInfo）
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ requests(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) { pageInfo { hasNextPage endCursor } totalCount edges { node { id modelID createdAt } } } }"
  }' | jq '.'

# 翻下一页（把上面的 endCursor 填入 after）
curl -s -X POST "$AXONHUB_BASE/admin/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ requests(first: 20, after: \"<endCursor>\", orderBy: {field: CREATED_AT, direction: DESC}) { pageInfo { hasNextPage endCursor } edges { node { id modelID createdAt } } } }"
  }' | jq '.'
```

---

## Request 对象字段速查

| 字段 | 说明 |
|------|------|
| `id` | 请求 ID |
| `modelID` | 请求的模型名 |
| `status` | `pending` / `processing` / `completed` / `failed` / `canceled` |
| `stream` | 是否是流式请求 |
| `source` | `api` / `playground` / `test` |
| `format` | API 格式（`openai` / `anthropic` 等）|
| `requestBody` | 完整请求体 JSON（可能为 null，已外存时用 REST 下载）|
| `responseBody` | 完整响应体 JSON（可能为 null）|
| `requestHeaders` | 请求头 JSON |
| `metricsLatencyMs` | 总延迟（毫秒）|
| `metricsFirstTokenLatencyMs` | 首 token 延迟（毫秒）|
| `metricsReasoningDurationMs` | 推理时长（毫秒，含 thinking 的模型）|
| `clientIP` | 客户端 IP |
| `traceID` | 所属 Trace ID（外键 ID，非 trace 字符串）|
| `channelID` | 路由到哪个 channel |
| `createdAt` | 请求时间 |

---

## 可选：OpenAPI GraphQL（service_account API key）

如果有 `service_account` 类型的 API Key，可以不用登录直接查询：

```bash
API_KEY="sk-your-service-account-key"

curl -s -X POST "$AXONHUB_BASE/openapi/v1/graphql" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ ... }"}' | jq '.'
```

> 注意：目前 OpenAPI GraphQL schema 较小，主要支持 `createLLMAPIKey`，不支持完整的 requests 查询。推荐优先使用 `/admin/graphql`。

---

## 直接查询 SQLite（本地部署时）

```bash
DB_PATH=$(grep "dsn:" ~/.config/axonhub/config.yml | sed 's/.*dsn: *"//' | sed 's/?.*//' | tr -d '"')

# 最近 20 条请求
sqlite3 "$DB_PATH" "
SELECT id, model_id, status, created_at, metrics_latency_ms
FROM requests
ORDER BY created_at DESC
LIMIT 20;
"

# 按 trace_id 查
sqlite3 "$DB_PATH" "
SELECT r.id, r.model_id, r.status, u.total_tokens
FROM requests r
LEFT JOIN usage_logs u ON u.request_id = r.id
WHERE r.trace_id = (
  SELECT id FROM traces WHERE trace_id = 'at-demo-123' LIMIT 1
)
ORDER BY r.created_at ASC;
"
```

---

## 限制说明

- `requestBody` / `responseBody` 可能因外存设置（`contentSaved = true`）为 null，改用 `GET /admin/requests/:id/content`
- 无原生 CLI 工具或 MCP server，查询必须通过 GraphQL 或直接 SQL
- JWT token 会过期，请求 401 时重新登录获取
