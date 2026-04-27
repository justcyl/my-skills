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
  [--resolution 1K|2K|4K] \
  [--model gemini-3.1-flash-image-preview|gpt-image-2|grok-4.2-image]
```

**编辑已有图片：**
```bash
uv run <skill-dir>/scripts/generate_image.py \
  --prompt "editing instructions" \
  --filename "output-name.png" \
  --input-image "path/to/input.png" \
  [--resolution 1K|2K] [--model MODEL]
```

**生成并加入 Gallery：**
```bash
uv run <skill-dir>/scripts/generate_image.py \
  --prompt "..." \
  --filename "img.png" \
  --model gpt-image-2 \
  --gallery review.html
```

**仅重建 Gallery HTML（不生成图片）：**
```bash
uv run <skill-dir>/scripts/generate_image.py --gallery review.html
```

**重要：** 始终在用户的工作目录运行，图片和 gallery 保存在当前目录。

## 分辨率

- **1K**（默认）—— ~1024px
- **2K** —— ~2048px
- **4K** —— ~4096px（仅建议用于 gpt-image-2，其他模型忽略此参数）

> gemini 和 grok 的分辨率由代理服务端决定，无法通过参数精确控制；`--resolution` 仅作为提示传入 prompt。

## Gallery 功能

`--gallery <html文件>` 开启 Gallery 模式：
- 每次生成成功后，自动将图片追加到 Gallery HTML 文件
- 同时维护一个 `<gallery-name>.meta.json` 元数据文件（存储模型、prompt、尺寸、时间戳等）
- 生成的 HTML 是**自包含**的静态文件，用浏览器打开即可
- 支持按模型、审批状态筛选，支持 prompt 搜索
- 审批状态（approve / reject）存储在 `localStorage`，刷新后保留
- 点击图片可放大查看（Lightbox）

**典型批量生成 + 审批工作流：**
```bash
# 生成一批不同风格/模型的图
uv run .../generate_image.py --prompt "..." --filename "a.png" --model gemini-3.1-flash-image-preview --gallery review.html
uv run .../generate_image.py --prompt "..." --filename "b.png" --model gpt-image-2 --resolution 2K  --gallery review.html
uv run .../generate_image.py --prompt "..." --filename "c.png" --model grok-4.2-image               --gallery review.html

# 打开 review.html 在浏览器中审批
open review.html
```

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
