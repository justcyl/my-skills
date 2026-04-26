---
name: gemini-image-gen
description: >
  Generate/edit images with Gemini image models (default: gemini-3.1-flash-image-preview).
  Use for any image create/modify request. Supports text-to-image + image-to-image editing;
  1K/2K/4K resolution; base-url gateways and provider fallback (gemini-native/openai-chat-compat).
  Use --model to select a different model.
---

# Gemini Image Generation & Editing

通用图片生成/编辑工具，基于 Google Gemini 图像生成 API。

> **本 skill 不含任何领域特化逻辑。** 学术论文配图请使用 `academic-paper` skill 的配图子模块，它会调用本 skill 作为底层引擎。

## Usage

脚本位于 `scripts/generate_image.py`（相对于本 SKILL.md 所在目录）。运行前先解析完整路径。

**生成新图片：**
```bash
uv run <this-skill-directory>/scripts/generate_image.py \
  --prompt "your image description" \
  --filename "output-name.png" \
  [--resolution 1K|2K|4K] [--model MODEL] [--api-key KEY] \
  [--base-url URL] [--provider auto|gemini-native|openai-chat-compat]
```

**编辑已有图片：**
```bash
uv run <this-skill-directory>/scripts/generate_image.py \
  --prompt "editing instructions" \
  --filename "output-name.png" \
  --input-image "path/to/input.png" \
  [--resolution 1K|2K|4K] [--model MODEL]
```

**重要：** 始终在用户的工作目录运行，图片保存在当前目录而非 skill 目录。

## Resolution

- **1K** (default) — ~1024px
- **2K** — ~2048px
- **4K** — ~4096px

编辑模式下，若未指定分辨率，自动匹配输入图片尺寸。

## Model

默认 `gemini-3.1-flash-image-preview`。可选：
- `gemini-3.1-flash-image-preview` — 快速
- `gemini-3-pro-image-preview` — 高质量，较慢

## Provider & Gateway

- `auto` (default): 先 gemini-native，失败则 fallback openai-chat-compat
- `gemini-native`: 强制 Gemini SDK
- `openai-chat-compat`: 强制 `/v1/chat/completions`

网关示例：
```bash
uv run ... --base-url "https://api.ikuncode.cc" --provider auto
```

可选重试参数：`--max-retries 3` / `--retry-backoff-ms 1200` / `--timeout-ms 60000`

## API Key

优先级：`--api-key` > `~/.config/inno-figure-gen/config.env` 中的 `INNO_FIGURE_GEN_API_KEY` > `GEMINI_API_KEY` 环境变量。

配置文件 `~/.config/inno-figure-gen/config.env`：
```env
INNO_FIGURE_GEN_API_KEY=sk-xxx
INNO_FIGURE_GEN_BASE_URL=https://your-gateway.example.com
INNO_FIGURE_GEN_DEFAULT_MODEL=gemini-3.1-flash-image-preview
```

## Prompt Handling

- **生成：** 直接传递用户描述。仅在明显不足时补充。
- **编辑：** 传递编辑指令（如 "remove the background", "change to cartoon style"）。

通用模板：
- 生成：`"Create an image of: <subject>. Style: <style>. Background: <bg>. Color palette: <palette>. Avoid: <list>."`
- 编辑（保持其余不变）：`"Change ONLY: <single change>. Keep identical: subject, composition, pose, lighting, color palette, background, text, and overall style."`

## Filename

格式：`yyyy-mm-dd-hh-mm-ss-descriptive-name.png`

## Post-Generation Figure Check (Optional)

生成图片后，可以选择性地调用 `pi-subagent` 的 `figure-qa` agent 做视觉质量检查。

调用方式详见 [`pi-subagent/agents/figure-qa.md`](../pi-subagent/agents/figure-qa.md)，使用以下参数：

```
Scene:  general
Intent: <original prompt summary>
```

- **默认关闭**：gemini-image-gen 是通用工具，不强制检查
- 专用 skill（`academic-paper`、`rhetoric-of-decks`）已内置 figure-qa 集成
- figure-qa 会自动压缩图片再审查，不会撑爆上下文
- 若报告返回 ❌ REGENERATE，根据 Regeneration Guidance 构造修复 prompt，使用 `--input-image` 重新生成

## Preflight

```bash
command -v uv                    # 必须存在
test -n "$GEMINI_API_KEY"        # 或传 --api-key
test -f "path/to/input.png"      # 编辑模式需验证输入文件
```

## Output

- PNG 保存到当前目录
- 脚本输出完整路径
- **不要回读图片内容** — 只告知用户保存路径
