# 配图生成（figure-gen）

为学术论文生成 publication-quality 概念图：架构图、pipeline、概念图、对比图。

> 数据驱动图表（bar chart / line plot / heatmap）不属于本模块，用 matplotlib/seaborn 直接绘制。

底层引擎：**image-gen** skill 的 `generate_image.py`（支持 gemini-3.1-flash-image-preview / gpt-image-2 / grok-4.2-image）。视觉审查：**pi-subagent** skill 的 `figure-qa` agent（scene: `academic`）。

---

## 模型选择

| 模型 | 适用场景 | 分辨率支持 |
|------|---------|----------|
| `gemini-3.1-flash-image-preview` | **默认**，快速草稿，概念图 / pipeline | 自动 (~1K) |
| `gpt-image-2` | 高质量终稿，layout 精细时首选 | ✅ 1K / 2K |
| `grok-4.2-image` | 风格多样性探索 | 固定 ~2K |

> 推荐策略：草稿阶段用 `gemini-3.1-flash-image-preview`（速度快，迭代成本低）；通过 figure-qa 后，终稿用 `gpt-image-2 --resolution 2K` 提升精度。

---

## 配图类型

| 类型 | 典型用途 | 关键词 |
|------|---------|--------|
| `architecture` | Method Overview / 模型架构 / Figure 1 | 架构图、framework、model overview |
| `pipeline` | 多步骤流程 / 数据处理 | pipeline、workflow、流程图 |
| `concept` | 动机说明 / 直觉示意 / 问题定义 | concept、motivation、intuition |
| `comparison` | A vs B / Before-After | 对比、comparison、vs |

---

## Prompt 工程

### 通用学术约束（每个 prompt 末尾必须追加）

```
CRITICAL STYLE REQUIREMENTS:
- Flat vector illustration style, clean lines, minimalist academic aesthetic
- Background: pure white (#FFFFFF), absolutely no texture, gradient, or pattern
- Color palette: muted pastel tones only (soft blue, warm orange, sage green, light gray)
- NO photorealistic rendering, NO 3D shadows, NO glossy/metallic effects
- NO decorative elements, NO ornamental borders, NO watermarks
- Clean geometric shapes: rectangles, rounded rectangles, circles, arrows
- Professional and restrained — this is for a top-tier academic paper, not a poster
```

### 类型专用前缀

**architecture:**

```
Create a technical architecture diagram for an academic paper.
Layout: clear left-to-right or top-to-bottom data flow.
Components: labeled rectangular modules with short English text inside.
Connections: clean directional arrows showing data/information flow.
Group related components with subtle light-colored background regions.
```

**pipeline:**

```
Create a horizontal step-by-step pipeline diagram for an academic paper.
Each processing stage is a rounded rectangle with a concise English label.
Stages connected by clean arrows. Use subtle color coding to distinguish phases.
```

**concept:**

```
Create a minimal conceptual illustration for an academic paper.
Use simple abstract geometric shapes to convey the idea.
Maximum clarity, minimum detail. Focus on the core insight.
If showing a problem/solution contrast, use clear spatial separation.
```

**comparison:**

```
Create a side-by-side comparison diagram for an academic paper.
Clear visual separation between panels (left vs right, or top vs bottom).
Use consistent visual encoding across panels so differences are obvious.
Label each panel clearly. Highlight key differences with color or annotation.
```

### 文字处理策略

Gemini 的图内文字容易出现乱码/拼错，采用两阶段策略：

**阶段 1 — 带文字生成（先尝试）：** 在 prompt 中明确列出所有标签：

```
Text labels that MUST appear exactly as written:
- "Encoder" (inside the blue rectangle on the left)
- "Attention" (inside the orange rectangle in the center)
- "Decoder" (inside the green rectangle on the right)
```

**阶段 2 — 无文字模式（文字渲染失败时切换）：**

```
IMPORTANT: Do NOT render any text, letters, words, or characters inside the image.
Leave clean blank spaces where labels would go. Text will be added in post-processing.
```

然后用 draw.io / Figma / PowerPoint 叠加文字标注。

---

## 工作流

### Step 1 — 理解需求

1. 判断图片类型（architecture / pipeline / concept / comparison）
2. 提取需出现在图中的关键模块名称和连接关系
3. 确认输出尺寸（单栏 `\columnwidth` 还是双栏 `\textwidth`）

### Step 2 — 构造 Prompt

按顺序拼接：`[类型专用前缀]` + `[具体内容]` + `[文字标签列表]` + `[通用学术约束]`

### Step 3 — 1K 草稿生成

使用 image-gen，`--resolution 1K` 快速出稿，同时开启 gallery 追踪：

```bash
uv run <image-gen-dir>/scripts/generate_image.py \
  --prompt "<完整 prompt>" \
  --filename "figures/<name>-draft.png" \
  --model gemini-3.1-flash-image-preview \
  --resolution 1K \
  --gallery figures-gallery.html
```

> `--gallery figures-gallery.html` 会在当前工作目录创建/更新 gallery。**每一次生成（草稿、修复轮次、终稿）都带上此参数**，所有候选版本自动积累到 gallery 中，供用户事后对比。

### Step 4 — figure-qa 审查（最多 3 轮）

调用 `pi-subagent` 的 `figure-qa` agent，调用方式详见 [`pi-subagent/agents/figure-qa.md`](../pi-subagent/agents/figure-qa.md)，使用以下参数：

```
Scene:  academic
Intent: <一句话描述图应该展示什么>
Extra:  Figure type: <type>. Required labels: <list>.
```

| 结果 | 处理 |
|------|------|
| ✅ PASS | → Step 5 |
| ⚠️ MINOR | 可选修复，或直接 → Step 5 |
| ❌ REGENERATE | 根据 Regeneration Guidance 用 `--input-image` 编辑修复，再次检查 |

**3 轮未通过** → 保存当前最佳版本，告知用户具体不足，建议 draw.io / Figma / TikZ 手动微调。

### Step 5 — 2K 终稿

草稿确认后，用相同 prompt 切换 `gpt-image-2 --resolution 2K` 生成高分辨率终稿（同样追加到 gallery）：

```bash
uv run <image-gen-dir>/scripts/generate_image.py \
  --prompt "<完整 prompt>" \
  --filename "figures/<name>-final.png" \
  --model gpt-image-2 \
  --resolution 2K \
  --gallery figures-gallery.html
```

> 若 gpt-image-2 风格与草稿偏差过大，可继续用 `gemini-3.1-flash-image-preview --input-image <draft>` 迭代。

### Step 6 — 插入 LaTeX + 输出 Gallery

将终稿插入 LaTeX（`figures/<name>-final.png`），**不等用户审批，直接完成插入**。全部图片生成完毕后，向用户汇报：

```
✅ 所有配图已生成并插入 LaTeX。

📁 备选 gallery：figures-gallery.html
   共 N 张候选图（包含所有草稿和终稿）。
   用浏览器打开即可逐图 Approve / Reject，如需替换某张图，
   将对应候选文件复制到 figures/<name>-final.png 并重新编译即可。
```

> **Gallery 不阻塞流程**。论文已处于可编译状态，gallery 只是备用审查工具。

### Step 7 — LaTeX Snippet

**双栏图（architecture / pipeline）：**

```latex
\begin{figure*}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{figures/method.png}
  \caption{Overview of our method. <self-contained description>.}
  \label{fig:method}
\end{figure*}
```

**单栏图（concept / comparison）：**

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{figures/concept.png}
  \caption{<Caption.>}
  \label{fig:concept}
\end{figure}
```

Caption 要求：self-contained（不读正文也能理解）；描述"图里有什么 + 关键结构/发现"；缩写首次在 caption 出现时展开。

---

## 已知限制

| 限制 | 建议 |
|------|------|
| 文字渲染不稳定（乱码/拼错） | 复杂标注切换无文字模式，后期手动叠加 |
| 几何精度有限（对齐/等距） | 容忍轻微不对称，或用 TikZ 精确绘制 |
| 跨图风格一致性 | 用 `--input-image` 以前一张图作为参考 |
| 不适用于数据图表 | 折线图/柱状图/热力图请用 matplotlib |
