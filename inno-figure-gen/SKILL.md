---
name: inno-figure-gen
description: >
  Generate/edit images with Gemini image models (default:
  gemini-3.1-flash-image-preview). Use for image create/modify requests incl.
  edits. Supports text-to-image + image-to-image; 1K/2K/4K; use --input-image;
  supports base-url gateways and provider fallback
  (gemini-native/openai-chat-compat). Use --model to select a different model.
---

# Gemini Image Generation & Editing

Generate new images or edit existing ones using Google's Gemini image generation API (default model: `gemini-3.1-flash-image-preview`).

## 中文快速说明

- 适用场景：根据文本生成图片，或基于已有图片做定向编辑。
- 运行方式：通过 `uv run` 执行当前 skill 目录下的 `scripts/generate_image.py`。
- 输出位置：图片输出到你执行命令时的当前工作目录（由 `--filename` 决定）。
- 网关兼容：可通过 `--base-url` 接入中转网关，默认 `--provider auto` 自动回退调用路径。
- 密钥建议：优先使用环境变量 `GEMINI_API_KEY`，避免在命令参数中明文传 `--api-key`。

## Usage

The script is at `scripts/generate_image.py` **relative to this skill's directory** (the directory containing this `SKILL.md`). Resolve the full path from the skill's location before running. Do not hardcode `~/.codex/...`, because the skill may be installed in a different location.

Keep the distinction clear:
- The **script path** tells you where to find `generate_image.py`.
- The **output path** is controlled by the current working directory plus `--filename`.
- Run from the user's working directory so relative filenames save output there, not in the skill directory.

**Generate new image:**
```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "your image description" --filename "output-name.png" [--resolution 1K|2K|4K] [--model MODEL] [--api-key KEY] [--base-url URL] [--provider auto|gemini-native|openai-chat-compat]
```

**Edit existing image:**
```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "editing instructions" --filename "output-name.png" --input-image "path/to/input.png" [--resolution 1K|2K|4K] [--model MODEL] [--api-key KEY] [--base-url URL] [--provider auto|gemini-native|openai-chat-compat]
```

**Important:** Always run from the user's current working directory so images are saved where the user is working, not in the skill directory.

## Default Workflow (draft → iterate → final)

Goal: fast iteration without burning time on 4K until the prompt is correct.

- Draft (1K): quick feedback loop
  - `uv run <this-skill-directory>/scripts/generate_image.py --prompt "<draft prompt>" --filename "yyyy-mm-dd-hh-mm-ss-draft.png" --resolution 1K`
- Iterate: adjust prompt in small diffs; keep filename new per run
  - If editing: keep the same `--input-image` for every iteration until you’re happy.
- Final (4K): only when prompt is locked
  - `uv run <this-skill-directory>/scripts/generate_image.py --prompt "<final prompt>" --filename "yyyy-mm-dd-hh-mm-ss-final.png" --resolution 4K`

## Resolution Options

The Gemini 3 Pro Image API supports three resolutions (uppercase K required):

- **1K** (default) - ~1024px resolution
- **2K** - ~2048px resolution
- **4K** - ~4096px resolution

Map user requests to API parameters:
- No mention of resolution → `1K`
- "low resolution", "1080", "1080p", "1K" → `1K`
- "2K", "2048", "normal", "medium resolution" → `2K`
- "high resolution", "high-res", "hi-res", "4K", "ultra" → `4K`

## Model Selection

The default model is `gemini-3.1-flash-image-preview`. You can override it with the `--model` flag:

```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "..." --filename "..." --model gemini-3.1-flash-image-preview
```

Available models depend on your Gemini API access. Common options:
- `gemini-3.1-flash-image-preview` (default) - Fast image generation
- `gemini-3-pro-image-preview` - Higher quality, slower

## Provider And Gateway Modes

`generate_image.py` now supports three provider modes:

- `auto` (default): try `gemini-native` first, then fallback to `openai-chat-compat` if needed
- `gemini-native`: force Gemini SDK native call path
- `openai-chat-compat`: force `/v1/chat/completions` compatible path

For gateway usage, set `--base-url`:

```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "A cute orange cat" --filename "cat.png" --model gemini-3.1-flash-image-preview --base-url "https://api.ikuncode.cc" --provider auto
```

Explicitly force OpenAI-compatible path:

```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "A red apple on white background" --filename "apple.png" --model gemini-3.1-flash-image-preview --base-url "https://api.ikuncode.cc" --provider openai-chat-compat
```

Optional resilience flags:
- `--max-retries` (default `3`)
- `--retry-backoff-ms` (default `1200`)
- `--timeout-ms` (default `60000`)

## API Key

The script checks for API key in this order:
1. `--api-key` argument (use if user provided key in chat)
2. `GEMINI_API_KEY` environment variable

If neither is available, the script exits with an error message.

## Preflight + Common Failures (fast fixes)

- Preflight:
  - `command -v uv` (must exist)
  - `test -n \"$GEMINI_API_KEY\"` (or pass `--api-key`)
  - If editing: `test -f \"path/to/input.png\"`

- Common failures:
  - `Error: No API key provided.` → set `GEMINI_API_KEY` or pass `--api-key`
  - `Error loading input image:` → wrong path / unreadable file; verify `--input-image` points to a real image
  - “quota/permission/403” style API errors → wrong key, no access, or quota exceeded; try a different key/account
  - `system_cpu_overloaded` / `error code: 524` → transient gateway issue; script auto-retries, rerun if needed
  - `model_not_found` on one path → use `--provider auto` or switch model/provider

## Filename Generation

Generate filenames with the pattern: `yyyy-mm-dd-hh-mm-ss-name.png`

**Format:** `{timestamp}-{descriptive-name}.png`
- Timestamp: Current date/time in format `yyyy-mm-dd-hh-mm-ss` (24-hour format)
- Name: Descriptive lowercase text with hyphens
- Keep the descriptive part concise (1-5 words typically)
- Use context from user's prompt or conversation
- If unclear, use random identifier (e.g., `x9k2`, `a7b3`)

Examples:
- Prompt "A serene Japanese garden" → `2025-11-23-14-23-05-japanese-garden.png`
- Prompt "sunset over mountains" → `2025-11-23-15-30-12-sunset-mountains.png`
- Prompt "create an image of a robot" → `2025-11-23-16-45-33-robot.png`
- Unclear context → `2025-11-23-17-12-48-x9k2.png`

## Image Editing

When the user wants to modify an existing image:
1. Check if they provide an image path or reference an image in the current directory
2. Use `--input-image` parameter with the path to the image
3. The prompt should contain editing instructions (e.g., "make the sky more dramatic", "remove the person", "change to cartoon style")
4. Common editing tasks: add/remove elements, change style, adjust colors, blur background, etc.

## Prompt Handling

**For generation:** Pass user's image description as-is to `--prompt`. Only rework if clearly insufficient.

**For editing:** Pass editing instructions in `--prompt` (e.g., "add a rainbow in the sky", "make it look like a watercolor painting")

Preserve user's creative intent in both cases.

## Prompt Templates (high hit-rate)

Use templates when the user is vague or when edits must be precise.

- Generation template:
  - “Create an image of: <subject>. Style: <style>. Composition: <camera/shot>. Lighting: <lighting>. Background: <background>. Color palette: <palette>. Avoid: <list>.”

- Editing template (preserve everything else):
  - “Change ONLY: <single change>. Keep identical: subject, composition/crop, pose, lighting, color palette, background, text, and overall style. Do not add new objects. If text exists, keep it unchanged.”

## Output

- Saves PNG to current directory (or specified path if filename includes directory)
- Script outputs the full path to the generated image
- **Do not read the image back** - just inform the user of the saved path

## Examples

**Generate new image:**
```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "A serene Japanese garden with cherry blossoms" --filename "2025-11-23-14-23-05-japanese-garden.png" --resolution 4K
```

**Edit existing image:**
```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "make the sky more dramatic with storm clouds" --filename "2025-11-23-14-25-30-dramatic-sky.png" --input-image "original-photo.jpg" --resolution 2K
```

**Gateway mode with fallback:**
```bash
uv run <this-skill-directory>/scripts/generate_image.py --prompt "一只卡通橘猫坐在草地上，阳光明亮，插画风格" --filename "2026-04-02-14-00-00-cat.png" --model gemini-3.1-flash-image-preview --base-url "https://api.ikuncode.cc" --provider auto
```
