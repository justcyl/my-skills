---
name: web-reader
description: |
  将任意网页转为干净的 Markdown 供 LLM 消费。基于 Jina Reader API，适用于网页研究、文档阅读、内容提取等场景。
  当用户需要阅读网页、获取在线文档、或从 URL 提取信息时使用。
allowed-tools:
  - WebFetch
  - Bash
  - Read
  - Write
  - Edit
---

# Web Reader — 网页内容提取与阅读

将任意网页 URL 转为 LLM 友好的 Markdown，用于研究、文档阅读和信息提取。

## 何时使用

- 用户提供了一个 URL，希望了解其内容
- 需要阅读在线文档、博客文章或技术资料
- 需要从网页提取结构化信息（表格、列表、代码块等）
- WebFetch 直接读取效果不佳（动态渲染页面、复杂布局）
- 需要批量读取多个网页并汇总
- 需要搜索网页内容并获取 LLM 友好的结果

## 核心原理

在任意 URL 前添加 `https://r.jina.ai/` 前缀，Jina Reader 会：

1. 使用无头浏览器渲染页面（支持 SPA、动态内容）
2. 提取正文内容，过滤导航栏、广告等噪音
3. 转为干净的 Markdown 格式返回

## 两大端点

| 端点 | 格式 | 用途 |
|------|------|------|
| `r.jina.ai` | `https://r.jina.ai/{URL}` | 读取单个 URL 内容 |
| `s.jina.ai` | `https://s.jina.ai/{查询词}` | 搜索网页，返回 top 5 结果 |

## 使用方式

### 方式 1：WebFetch（推荐）

通过 WebFetch 工具直接调用，prompt 参数用于指导内容提取：

```
WebFetch("https://r.jina.ai/https://example.com/docs/api", "提取所有 API 端点及其参数说明")
```

```
WebFetch("https://r.jina.ai/https://blog.example.com/post", "总结这篇文章的核心观点")
```

### 方式 2：curl（需要精细控制时）

```bash
# 基础读取
curl -s "https://r.jina.ai/https://example.com"

# 获取 JSON 格式响应（含 url、title、content 字段）
curl -s -H "Accept: application/json" "https://r.jina.ai/https://example.com" | jq '.data'

# 仅提取页面特定区域
curl -s -H "x-target-selector: .main-content" "https://r.jina.ai/https://example.com"

# 等待动态内容加载后再提取
curl -s -H "x-wait-for-selector: #loaded" -H "x-timeout: 10" "https://r.jina.ai/https://example.com"

# 网页搜索
curl -s "https://s.jina.ai/how%20to%20use%20jina%20reader"

# 限定站点搜索
curl -s "https://s.jina.ai/query?site=docs.example.com"
```

## HTTP Headers 速查

| Header | 值 | 用途 |
|--------|-----|------|
| `x-respond-with` | `markdown` / `html` / `text` / `screenshot` | 控制输出格式（默认 markdown） |
| `x-target-selector` | CSS 选择器 | 仅提取页面指定区域 |
| `x-wait-for-selector` | CSS 选择器 | 等待元素渲染后再提取 |
| `x-timeout` | 秒数 | 设置等待超时 |
| `x-with-generated-alt` | `true` | 为图片生成描述性 alt 文本 |
| `x-no-cache` | `true` | 绕过缓存获取最新内容 |
| `x-cache-tolerance` | 秒数 | 缓存容忍时间（默认 3600s） |
| `x-set-cookie` | cookie 字符串 | 转发 cookie（会禁用缓存） |
| `x-proxy-url` | 代理 URL | 通过代理访问 |
| `Accept` | `application/json` | 返回 JSON 格式 |
| `Accept` | `text/event-stream` | 流式返回 |

## 典型场景

### 场景 1：阅读技术文档

```
WebFetch("https://r.jina.ai/https://docs.python.org/3/library/asyncio.html", "提取 asyncio 的核心概念和常用 API")
```

### 场景 2：研究竞品或工具

```
WebFetch("https://r.jina.ai/https://some-tool.dev/features", "列出所有功能特性及其描述")
```

### 场景 3：搜索并汇总

先搜索，再逐个读取有价值的结果：

```
# 第一步：搜索
WebFetch("https://s.jina.ai/rust async runtime comparison 2025", "列出搜索结果的标题和 URL")

# 第二步：读取感兴趣的结果
WebFetch("https://r.jina.ai/{result_url}", "提取关键对比结论")
```

### 场景 4：提取页面特定部分

需要精细控制时用 curl + CSS 选择器：

```bash
# 只提取 API 参考部分
curl -s -H "x-target-selector: #api-reference" "https://r.jina.ai/https://docs.example.com"
```

### 场景 5：保存网页内容到本地

```bash
# 将网页内容保存为 Markdown 文件
curl -s "https://r.jina.ai/https://example.com/article" > /tmp/article.md
```

## 策略选择

| 场景 | 推荐方式 |
|------|---------|
| 快速阅读单个网页 | WebFetch + `r.jina.ai` |
| 需要定向提取信息 | WebFetch + prompt 引导 |
| 动态页面 / 需要等待渲染 | curl + `x-wait-for-selector` |
| 仅提取页面局部 | curl + `x-target-selector` |
| 搜索互联网内容 | WebFetch + `s.jina.ai` |
| 需要 JSON 结构化响应 | curl + `Accept: application/json` |
| 需要保留原始 HTML | curl + `x-respond-with: html` |

## 限制

- **速率限制**：无 API Key 时 20 RPM，免费 Key 500 RPM
- **搜索端点**：无 Key 不可用，需注册免费 Key
- **缓存**：默认缓存 3600s，用 `x-no-cache: true` 绕过
- **付费墙/登录页**：无法穿透需要认证的页面（可用 `x-set-cookie` 转发 cookie）
- **超大页面**：内容可能被截断，配合 `x-target-selector` 缩小范围
