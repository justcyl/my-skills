# Agent CLI Patterns

当为 agent 设计新 CLI 的命令面时，使用本参考。

## Mental Model

CLI 是 agent 的命令层。它应该把服务、app、API、日志源或数据库，变成 agent 可以从任意 repo 重复调用的 shell 命令。

好的 agent CLI 暴露可组合的原语。避免把"做完整调查"塞进单个命令——更小的 discover、read、resolve、download、inspect、draft、upload 命令组合起来效果更好。

## Help 是接口

`--help` 是写给只有二进制和模糊任务的 future agent 看的。每个命令应有简短描述，flag 使用产品或 API 的字面名称。

好的顶层 help 应能回答：

- 能发现哪些容器？
- 能精确读取哪些对象？
- 能把什么解析为稳定 ID？
- 能下载或上传哪些文件？
- 有哪些写操作？
- Raw escape hatch 是什么？

## 推荐命令形态

使用产品名词 + 动词：

```bash
tool-name --json doctor
tool-name --json accounts list
tool-name --json projects list
tool-name --json channels resolve --name general
tool-name --json messages search "exact phrase"
tool-name --json messages context <message-id> --before 3 --after 3
tool-name --json logs download <build-url> --failed --out ./logs
tool-name --json media upload --file ./image.png
tool-name --json drafts create --body-file draft.json
```

对于原生名词已足够强的 API，直接动词也可以：

```bash
tool-name --json social-sets
tool-name --json drafts list --social-set <id>
tool-name --json request get /v2/me
```

重要规则是**一致性**。除非产品词汇要求，不要混用多种风格。

## 来自成熟 CLI 的有用形态

优先参考这些模式，而不是只适合 agent 的抽象：

```bash
# 字段选择结构化输出：让常见读操作可脚本化
tool-name issues list --json number,title,url,state
tool-name issues list --json number,title --jq '.[] | select(.state == "open")'

# 默认人类文本，按需完整 API 对象
tool-name pods get <name>
tool-name pods get <name> -o json

# 产品工作流命令，不只是 REST noun
tool-name logs tail
tool-name webhooks listen --forward-to localhost:4242/webhooks
tool-name webhooks trigger checkout.completed
```

只在用户确实需要时才实现过滤或模板化。稳定的 JSON 输出加上窄范围读命令是基线。

## Discovery → Resolve → Read → Context

按这个顺序设计第一批命令：

1. **Discover**：宽泛容器——workspaces、accounts、social sets、repos、projects、channels、queues。
2. **Resolve**：把人类输入转为 ID——用户名、频道名、permalink、PR URL、build URL、客户 slug。
3. **Read**：精确对象——issue、event、thread、draft、customer、job、run、media item。
4. **Context**：锚点周边信息（有用时）——附近消息、父 thread、周边日志、审计历史。

agent 已有稳定 ID 时，不要强迫它反复搜索。

## 文本、JSON、文件、退出码

如有帮助，默认支持人类文本。在 agent 需要解析或管道时，`--json` 处处可用。

`--json` 下：

- 只向 stdout 输出 JSON
- 进度和诊断信息发往 stderr
- 成功和错误结构已文档化
- 脱敏 token、cookie、客户密钥、私有 header 和无关 payload

下载和导出时：

- 尽可能写入用户提供的 `--out` 路径
- JSON 输出中返回文件路径、字节数（廉价时）、来源 URL 或 ID、以及后续命令

退出码：

- 命令成功（含空结果）时退出 0
- 认证失败、无效输入、网络失败、解析失败、API 错误、上传/下载不完整时退出非 0
- `doctor --json` 在 auth 缺失时也应可用——报告缺少 auth，而不是 crash

## 分页与广度

默认浅层返回，用显式旋钮控制广度：

```bash
tool-name --json messages search "topic" --limit 10
tool-name --json messages search "topic" --limit 50 --all-pages --max-pages 3
tool-name --json drafts list --limit 20 --offset 40
```

返回 `next_cursor`、`next_url`、`offset`、`page_count`，或 provider 实际提供的分页信息。

## Raw Escape Hatch

raw 命令是修复通道，不是主界面。

好的 raw 命令仍然使用已配置的 auth、base URL、JSON 解析、脱敏、状态/错误处理和 `--json`。

让只读调用容易：

```bash
tool-name --json request get /v2/me
```

把 raw write 视为 live write。不要把 POST/PUT/PATCH/DELETE 藏在 "debug" 命令里。

## Companion Skill 模式

companion skill 应比 CLI README 更小。它教的是通过工具的路径：

```md
Start with:

  tool-name --json doctor
  tool-name --json accounts list

For [common job]:

  tool-name --json ...
  tool-name --json ...

Rules:

- Prefer installed `tool-name` on PATH.
- Use --json when analyzing output.
- Create drafts by default.
- Do not publish/delete/retry/submit unless the user asked.
- Use `request get ...` only when high-level commands are missing.
```

只在 agent 需要选择下一个命令时，才包含 JSON 结构说明。
