---
name: image-gen
description: >
  多模型图片生成/编辑工具，通过本地代理统一调用 gemini-3.1-flash-image-preview、gpt-image-2、grok-4.2-image。
  支持 text-to-image、image-to-image 编辑、1K/2K 分辨率切换、以及 Gallery HTML 可视化审批（--gallery）。
  触发语境："画一张""生成图片""image generation""edit this image""生成一批图让我 review""图片 gallery"。
---

# image-gen

通用图片生成/编辑工具，支持多模型，通过本地代理服务统一调用。

> **本 skill 不含领域特化逻辑。** 学术论文配图、演示文稿配图等专用 skill 可调用本 skill 作为底层引擎。

## 支持的模型

| 模型 | 调用方式 | 分辨率控制 | 特点 |
|------|----------|-----------|------|
| `gemini-3.1-flash-image-preview` | `/v1/chat/completions` | 自动（~1K） | 速度快，默认模型 |
| `gpt-image-2` | `/v1/images/generations` | ✅ 1K/2K | 质量高，支持精确尺寸 |
| `grok-4.2-image` | `/v1/chat/completions` | 固定 ~2K | 返回远程 URL，自动下载 |

## 使用方法

脚本路径：`<skill-dir>/scripts/generate_image.py`（相对于本 SKILL.md 目录）。

**生成新图片：**
```bash
uv run <skill-dir>/scripts/generate_image.py \
  --prompt "your image description" \
  --filename "output-name.png" \
  [--session NAME] [--output-dir DIR] \
  [--resolution 1K|2K|4K] \
  [--model gemini-3.1-flash-image-preview|gpt-image-2|grok-4.2-image] \
  [--no-gallery]
```

**编辑已有图片：**
```bash
uv run <skill-dir>/scripts/generate_image.py \
  --prompt "editing instructions" \
  --filename "output-name.png" \
  --input-image "path/to/input.png" \
  [--session NAME] [--resolution 1K|2K]
```

**仅重建 Gallery HTML（不生成图片）：**
```bash
uv run <skill-dir>/scripts/generate_image.py --session NAME
# 或指定自定义目录
# uv run <skill-dir>/scripts/generate_image.py --output-dir ~/my-gallery
```

**重要：** 始终在用户的工作目录运行。

## 输出目录

| 情况 | 图片位置 | Gallery 位置 |
|------|---------|----------|
| 什么都不指定 | `~/.local/share/image-gen/apple.png` | `~/.local/share/image-gen/gallery.html` |
| `--session NAME` | `~/.local/share/image-gen/NAME/apple.png` | `~/.local/share/image-gen/NAME/gallery.html` |
| `--output-dir DIR` | `DIR/apple.png` | `DIR/gallery.html` |
| `--filename figures/foo.png`（含路径分隔符） | `<CWD>/figures/foo.png`（直接写入项目） | 不受影响，仍在 output-dir |
| `--no-gallery` | 同上 | 不创建 |

> **设计原则**：草稿 / 候选图和 gallery 默认不写入工作目录，避免污染项目。确认的终稿手动复制到项目（如 `figures/`）。

## 分辨率

- **1K**（默认）—— ~1024px
- **2K** —— ~2048px
- **4K** —— ~4096px（仅建议用于 gpt-image-2，其他模型忽略此参数）

> gemini 和 grok 的分辨率由代理服务端决定，无法通过参数精确控制；`--resolution` 仅作为提示传入 prompt。

## Gallery 功能

默认每次生成后自动建立/更新 Gallery，位于 output-dir 中，**不污染工作目录**。

`--session NAME` 常用来隔离不同任务的 gallery：

```bash
# 每次生成都属于同一个居名 session
uv run .../generate_image.py --prompt "..." --filename "a.png" --model gemini-3.1-flash-image-preview --session my-project
uv run .../generate_image.py --prompt "..." --filename "b.png" --model gpt-image-2 --resolution 2K      --session my-project
uv run .../generate_image.py --prompt "..." --filename "c.png" --model grok-4.2-image                   --session my-project

# Gallery 位于：~/.local/share/image-gen/my-project/gallery.html
open ~/.local/share/image-gen/my-project/gallery.html
```

如需在项目内用 `figures/method.png` 这种路径，图片会直接写入项目，而 gallery 仍在 session 目录：

```bash
uv run .../generate_image.py \
  --prompt "..." \
  --filename "figures/method.png" \
  --session my-paper
  # 图片 → <CWD>/figures/method.png
  # gallery → ~/.local/share/image-gen/my-paper/gallery.html
```

**Gallery HTML 功能：**
- 按模型、审批状态、prompt 关键词筛选
- Approve / Reject 按钒（状态存 `localStorage`，刷新后保留）
- 点击图片可放大（Lightbox）
- 配套同目录的 `.meta.json` 存储元数据

## Proxy 配置

代理服务已硬编码在脚本中，无需任何环境变量或配置文件：
- Base URL: `http://localhost:8090`
- API Key: 已内嵌（不暴露在 SKILL.md 中）

## Prompt 指南

- **生成**：直接传递描述，仅在明显不足时补充细节
- **编辑**：传递具体修改指令，如 "remove background" / "change to watercolor style"

模板：
- 生成：`"Create: <subject>. Style: <style>. Background: <bg>. Color palette: <palette>."`
- 编辑：`"Change ONLY: <single change>. Keep identical: composition, lighting, colors, style."`

## 文件名规范

格式：`yyyy-mm-dd-hh-mm-ss-descriptive-name.png`

## Post-Generation Check（可选）

生成后可调用 `pi-subagent` 的 `figure-qa` agent 做视觉质量检查（参数 `Scene: general`）。若返回 ❌ REGENERATE，根据建议构造修复 prompt 用 `--input-image` 重新生成。

## Preflight

```bash
command -v uv          # 必须存在
curl -s http://localhost:8090/v1/models -H "Authorization: Bearer <key>" | grep gpt-image-2
```
