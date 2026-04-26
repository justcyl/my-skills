# Pi Sub-Agent 模型路由表

本文件是人可读的参考文档。机器可读版本在 `scripts/models.sh`。

---

## 模型 Alias 列表

| alias | 模型字符串 | thinking | tools | 适用场景 |
|-------|-----------|----------|-------|---------|
| `gemini-pro` | `axonhub/gemini-3.1-pro-preview` | off | read,bash | 视觉理解、综合推理、图像 QA（默认）|
| `gemini-flash` | `axonhub/gemini-3.1-flash-preview` | off | read,bash | 快速、低成本任务、简单提取 |
| `gemini-think` | `axonhub/gemini-3.1-pro-preview` | on | read,bash | 需要深度推理的任务 |
| `claude-sonnet` | `anthropic/claude-sonnet-4-5` | off | read,bash | 代码生成、长文本理解、结构化输出 |
| `claude-think` | `anthropic/claude-opus-4` | on | read,bash | 复杂规划、多步推理、高难度分析 |

> **扩展方式**：在此表格增加一行，并在 `scripts/models.sh` 的 `resolve_model()` 函数中增加对应 `case` 分支。

---

## Agent 目录

| agent name | 文件 | 默认模型 | 功能描述 |
|-----------|------|---------|---------|
| `figure-qa` | `agents/figure-qa.md` | `gemini-pro` | AI 生成图片视觉 QA，输出结构化 Figure QA Report |

> **扩展方式**：在 `agents/` 下新建 `<name>.md`（frontmatter + system prompt），然后在上表增加一行说明。

---

## Invoke 参数说明

```
invoke.sh --agent <agent-name> [--model <alias>] --msg '<message>'
```

- `--agent`：必填，对应 `agents/<name>.md`
- `--model`：可选，覆盖 agent frontmatter 中的 `model` 字段；使用上表中的 alias
- `--msg`：必填，传给 sub-agent 的用户消息；支持 `\n` 换行

---

## 添加新模型 Alias

1. 在上方表格增加一行
2. 编辑 `scripts/models.sh`，在 `resolve_model()` 的 `case` 语句中增加分支：
   ```bash
   my-alias) echo "provider/model-string thinking-value tools-list" ;;
   ```
3. 格式固定为三列，空格分隔：`<model_string> <thinking_on_or_off> <tools_comma_separated>`
