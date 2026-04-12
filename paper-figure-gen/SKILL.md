---
name: paper-figure-gen
description: >
  为学术论文生成 publication-quality 图片（架构图、pipeline、概念示意图、对比图等）。
  内置学术 prompt 工程、强制 inspect-revise 循环、LaTeX snippet 输出。
  底层调用 gemini-image-gen skill 的 generate_image.py 引擎。
  适用场景："画个架构图"、"generate a figure for my paper"、"论文配图"、"method overview diagram"。
argument-hint: [figure-description-or-paper-context]
---

# Paper Figure Generator

为学术论文生成高质量配图。专注于解决论文中 **需要设计感的非数据图**：架构图、pipeline 示意图、概念图、对比图等——即 ARIS paper-figure skill 标记为「❌ No — manual」的那 ~40%。

> **数据驱动图表**（bar chart / line plot / heatmap 等）不属于本 skill 范围，请用 matplotlib/seaborn 直接绘制。

## 依赖

本 skill 调用 `gemini-image-gen` skill 的 `scripts/generate_image.py` 作为生图引擎。
请先确认该 skill 已安装，并通过以下命令定位脚本路径：

```bash
# 在已安装的 skills 目录中查找引擎脚本
GEMINI_SCRIPT=$(find ~/.agents/skills/gemini-image-gen ~/.claude/skills/gemini-image-gen ~/.codex/skills/gemini-image-gen -name generate_image.py 2>/dev/null | head -1)
echo "Engine: $GEMINI_SCRIPT"
```

## Figure 类型分类

收到用户请求后，先判断图片类型：

| 类型 | 典型用途 | 关键词 |
|------|---------|--------|
| `architecture` | Method Overview / 模型架构 / Figure 1 hero 图 | 架构图、architecture、framework、model overview |
| `pipeline` | 多步骤流程 / 数据处理 pipeline | pipeline、workflow、流程图、processing steps |
| `concept` | 动机说明 / 直觉示意 / 问题定义 | concept、motivation、intuition、示意图、idea |
| `comparison` | A vs B 方法对比 / Before-After | 对比、comparison、vs、difference |

## 学术 Prompt 工程

### 通用学术约束（EVERY prompt 必须追加）

```
CRITICAL STYLE REQUIREMENTS:
- Flat vector illustration style, clean lines, minimalist academic aesthetic
- Background: pure white (#FFFFFF), absolutely no texture, gradient, or pattern
- Color palette: muted pastel tones only (soft blue, warm orange, sage green, light gray)
- NO photorealistic rendering, NO 3D shadows, NO glossy/metallic effects
- NO decorative elements, NO ornamental borders, NO watermarks
- Clean geometric shapes: rectangles, rounded rectangles, circles, arrows
- Professional and restrained — this is for a NeurIPS/ICML/CVPR paper, not a poster
```

### 类型专用 Prompt 前缀

**architecture:**
```
Create a technical architecture diagram for an academic paper.
Layout: clear left-to-right or top-to-bottom data flow.
Components: labeled rectangular modules with short English text inside.
Connections: clean directional arrows showing data/information flow.
Group related components with subtle light-colored background regions.
Hierarchy: main pathway should be visually dominant; auxiliary paths thinner.
```

**pipeline:**
```
Create a horizontal step-by-step pipeline diagram for an academic paper.
Each processing stage is a rounded rectangle with a concise English label.
Stages connected by clean arrows. Use subtle color coding to distinguish phases.
Include small icons or symbols inside stages only if they aid comprehension.
Keep it linear and easy to follow from left to right.
```

**concept:**
```
Create a minimal conceptual illustration for an academic paper.
Use simple abstract geometric shapes to convey the idea.
Maximum clarity, minimum detail. No literal or realistic depictions.
Focus on the core insight or contrast the paper is trying to communicate.
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

Gemini 生成的图内文字经常出现**乱码、拼错、缺字**问题。采用以下两阶段策略：

**阶段 1 — 先尝试带文字生成：**
在 prompt 中明确列出所有文字标签：
```
Text labels that MUST appear exactly as written (spell each correctly):
- "Encoder" (inside the blue rectangle on the left)
- "Attention" (inside the orange rectangle in the center)  
- "Decoder" (inside the green rectangle on the right)
```

**阶段 2 — 如果文字渲染失败，切换为无文字模式：**
将 prompt 替换为：
```
IMPORTANT: Do NOT render any text, letters, words, or characters inside the image.
Leave clean blank spaces where labels would go. Text will be added in post-processing.
```
然后告知用户需要手动用 draw.io / Figma / PowerPoint 叠加文字标注。

## 工作流

### Step 1: 理解需求

1. 阅读用户提供的论文/方法描述
2. 判断 figure 类型（architecture / pipeline / concept / comparison）
3. 提取需要出现在图中的关键模块名称和连接关系
4. 确认输出尺寸偏好（单栏 `0.48\textwidth` 还是双栏 `0.95\textwidth`）

### Step 2: 构造 Prompt

按以下顺序拼接 prompt：

```
[类型专用前缀]

[用户描述的具体内容——模块、流程、关系等]

[文字标签列表]

[通用学术约束]
```

### Step 3: 1K 草稿生成

```bash
uv run $GEMINI_SCRIPT \
  --prompt "<constructed prompt>" \
  --filename "figures/yyyy-mm-dd-hh-mm-ss-draft.png" \
  --resolution 1K
```

### Step 4: 强制 Inspect-Revise 循环（最多 3 轮）

生成后，**必须** 读取图片文件进行视觉审查。对照以下 checklist：

- [ ] **布局**：模块/步骤的排列是否清晰？数据流方向是否一致？
- [ ] **文字**：所有标签是否正确拼写、清晰可读？（如果不可读，转阶段 2 无文字模式）
- [ ] **色彩**：是否为淡色系？有无刺眼的高饱和色、霓虹色？
- [ ] **背景**：是否纯白？有无渐变、纹理、暗色区域？
- [ ] **风格**：是否扁平矢量？有无 3D 阴影、光泽效果、写实元素？
- [ ] **学术感**：放在 NeurIPS/ICML 论文里是否违和？

**如果任何一项不通过：**

使用 `--input-image` 编辑模式修复：

```bash
uv run $GEMINI_SCRIPT \
  --prompt "<specific fix instruction>" \
  --filename "figures/yyyy-mm-dd-hh-mm-ss-rev1.png" \
  --input-image "figures/<previous-draft>.png" \
  --resolution 1K
```

常用修复指令：
- `"Make the background pure white. Remove all shadows and gradient effects."`
- `"Simplify the shapes to flat rectangles. Remove 3D rendering."`
- `"Fix the text label 'Encoer' — it should be 'Encoder'."`
- `"Make colors more muted and pastel. Current blue is too saturated."`
- `"Add clearer arrows between the modules showing data flow direction."`

**最多迭代 3 轮。** 如果 3 轮后仍不满意：
1. 保存当前最佳版本
2. 告知用户当前结果及具体不足之处
3. 建议用 draw.io / Figma / TikZ 进行手动微调

### Step 5: 4K 终稿

草稿确认后，生成高分辨率终稿：

```bash
uv run $GEMINI_SCRIPT \
  --prompt "<same final prompt>" \
  --filename "figures/yyyy-mm-dd-hh-mm-ss-final.png" \
  --resolution 4K
```

### Step 6: LaTeX Snippet 输出

为用户生成可直接粘贴的 LaTeX 代码：

**单栏图（concept / comparison）：**
```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=0.48\textwidth]{figures/<filename>.png}
    \caption{<根据 prompt 内容生成 1-2 句描述性 caption>}
    \label{fig:<auto-label>}
\end{figure}
```

**双栏图（architecture / pipeline）：**
```latex
\begin{figure*}[t]
    \centering
    \includegraphics[width=0.95\textwidth]{figures/<filename>.png}
    \caption{<caption>}
    \label{fig:<auto-label>}
\end{figure*}
```

Caption 写作要求：
- 必须 self-contained（不读正文也能理解图的含义）
- 描述图中展示了什么 + 关键发现/结构
- 所有缩写首次出现时展开

## 输出产物

```
figures/
├── <timestamp>-draft.png        # 1K 草稿（可删除）
├── <timestamp>-rev1.png         # 修订版（可删除）
├── <timestamp>-final.png        # 4K 终稿 ← 论文使用这个
└── latex-snippets.tex           # LaTeX 引用代码
```

## 已知限制

1. **文字渲染不稳定**：Gemini 对图内文字的拼写和排版控制有限，复杂标注建议后期手动叠加
2. **几何精度有限**：对齐、等距、严格对称等要求难以精确满足
3. **跨图风格一致性**：多张图之间的风格统一需要使用 `--input-image` 以前一张图作为参考
4. **不适用于数据图表**：折线图、柱状图、热力图等请用 matplotlib/seaborn

## 与其他 skill 的关系

| Skill | 职责 | 何时使用 |
|-------|------|---------|
| **gemini-image-gen** | 通用 Gemini 生图引擎 | 任何非学术的图片生成/编辑 |
| **paper-figure-gen** (本 skill) | 学术论文概念图生成 | 架构图、pipeline、概念图、对比图 |
| aris-paper-figure | 数据驱动图表 (matplotlib) | 训练曲线、ablation bar chart、heatmap |
| ds-figure-polish | 图表质量审阅标准 | 任何图表的最终质量检查 |

## 设计参考

- Prompt 模板参考 [PaperForge prompt-library](https://github.com/QJHWC/PaperForge)「论文架构图」部分
- 质量标准参考 [DeepScientist ds-figure-polish](https://github.com/OpenLAIR/dr-claw) 的 render-inspect-revise 工作流
- Figure scope 参考 [ARIS paper-figure](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 的 can/cannot 矩阵
