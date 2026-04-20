---
name: academic-paper
description: >
  AI 学术论文全周期写作。覆盖选模板、文献调研、结构化写作、配图生成、格式检查、投稿前审查。
  内置论文配图（figure-gen）与格式检查（format-check）子模块。
  搭配 overleaf、gemini-image-gen、visual-checker 使用。
  触发语境："写论文""paper writing""投稿前检查""画个架构图""论文配图""格式检查""desk reject"。
---

# Academic Paper

AI 学术论文全周期写作 skill。从选模板到投稿前终审，一条龙覆盖。

## 搭配 Skills

| Skill | 用途 | 何时调用 |
|-------|------|---------|
| **overleaf** | LaTeX 项目的 git clone / push / 编译 / 下载 PDF | 整个写作流程中随时同步 |
| **gemini-image-gen** | Gemini 图片生成引擎（text-to-image / image-to-image） | 配图子模块的底层引擎 |
| **visual-checker** | 视觉 QA 子代理（pass/fail 报告 + 修复建议） | 配图审查、格式视觉审查 |
| **ph-paper-helper** | 论文检索、导入、BibTeX 导出 | 文献调研阶段 |

## 写作全流程

```
Phase 0  准备 ──→ Phase 1  结构 ──→ Phase 2  初稿 ──→ Phase 3  配图
   │                │                │                │
   ▼                ▼                ▼                ▼
 获取模板         拟定大纲         逐节写作         figure-gen 子模块
 克隆 Overleaf    分配页面预算     文献融入         inspect-revise 循环
                                                      │
Phase 6  投稿 ←── Phase 5  终审 ←── Phase 4  格式检查 ←┘
   │                │                │
   ▼                ▼                ▼
 push Overleaf    人工通读         format-check 子模块
 提交系统         语言润色         自动化 + 视觉审查
```

---

## Phase 0: 准备

### 0.1 确认目标会议与模板

**在写任何文字之前，必须先获取以下信息：**

1. **目标会议 + 年份**（如 NeurIPS 2025、ACL 2025）
2. **论文类型**（long / short / workshop / position）
3. **LaTeX 模板**

```bash
# 常见模板获取
# NeurIPS 2025
wget https://media.neurips.cc/Conferences/NeurIPS2025/Styles/neurips_2025.zip

# ICML 2025
wget https://media.icml.cc/Conferences/ICML2025/Styles/icml2025.zip

# ICLR 2025
wget https://github.com/ICLR/Master-Template/raw/master/iclr2025.zip

# ACL/ARR (通用)
wget https://github.com/acl-org/acl-style-files/archive/refs/heads/master.zip
```

4. **页数限制**（见下方速查表）
5. **DDL**（投稿截止日期）

### 0.2 页数速查

| 会议 | 投稿正文 | Camera-ready | 参考文献 | 备注 |
|------|---------|-------------|---------|------|
| NeurIPS | 10 页 | 10 页 | 不计 | 含图表，不含参考文献/附录 |
| ICML | 8 页 | 9 页 | 不计 | 不含参考文献/Impact/附录 |
| ICLR | 6-10 页 | 同投稿 | 不计 | 6 页下限（2025 新增）|
| ACL/ARR Long | 8 页 | 9 页 | 不计 | Limitations **必须有** |
| ACL/ARR Short | 4 页 | 5 页 | 不计 | 同上 |
| AAAI | 7 页 + 2 附加 | 同投稿 | **计入** | 唯一参考文献计入页数 |

### 0.3 初始化 Overleaf 项目

```bash
# 使用 overleaf skill 克隆项目
# overleaf: clone <project-url>
```

建立标准目录结构：

```
project/
  main.tex
  sections/
    abstract.tex
    introduction.tex
    related_work.tex
    method.tex
    experiments.tex
    conclusion.tex
    limitations.tex      # ACL/ARR 必需
    ethics.tex           # ICML 推荐
  figures/
  tables/
  references.bib
```

### 0.4 文献调研

使用 `ph-paper-helper` 检索相关工作：

```bash
# 搜索方向
ph search "topic keywords"

# 导入关键论文
ph add <paper-id>

# 导出 BibTeX
ph export --format bibtex > references.bib
```

---

## Phase 1: 结构

### 1.1 大纲

按会议页数限制分配页面预算：

```
# 以 8 页 ACL Long 为例
Introduction:     1.0 页  — 问题、动机、贡献
Related Work:     1.0 页  — 对比最相关工作
Method:           2.5 页  — 核心方法描述
Experiments:      2.5 页  — 实验设置 + 结果 + 分析
Conclusion:       0.5 页  — 总结 + 局限性概述
Limitations:      0.5 页  — 不计入页数但必须有
```

### 1.2 Contribution Statement

在写初稿前，先明确 3 个贡献点（不超过 3 个）：

```
1. We propose ...
2. We demonstrate ...
3. We release / We provide ...
```

这 3 点必须在 Introduction 末尾和 Abstract 中一致出现。

---

## Phase 2: 初稿

### 写作顺序（推荐）

```
Method → Experiments → Introduction → Related Work → Abstract → Conclusion → Limitations
```

原因：Method 最稳定，Abstract 依赖全文。

### 写作规范

- **每段第一句是 topic sentence**，说清本段主张
- **每个 claim 有 evidence**：数字、引用、实验
- **缩写首次使用时展开**：Large Language Model (LLM)
- **Figure/Table 在正文中必须被引用**：`as shown in Figure~\ref{fig:xxx}`
- **引用用 `\citep{}` / `\citet{}`**，不要手动写 `[1]`
- **数字格式**：小数点后保留有效位数一致，大数用逗号分隔

### LaTeX 写作惯例

```latex
% 正确
Figure~\ref{fig:arch}       % 不可分割空格
Table~\ref{tab:results}
\citet{vaswani2017attention} propose ...
... achieved by \citep{devlin2019bert}.

% 错误
Figure \ref{fig:arch}       % 可能断行
[Vaswani et al., 2017]     % 手动引用
```

---

## Phase 3: 配图（figure-gen 子模块）

为学术论文生成 publication-quality 概念图：架构图、pipeline、概念图、对比图。

> **数据驱动图表**（bar chart / line plot / heatmap）不属于本模块，用 matplotlib/seaborn 直接绘制。

### 配图类型

| 类型 | 典型用途 | 关键词 |
|------|---------|--------|
| `architecture` | Method Overview / 模型架构 / Figure 1 | 架构图、framework |
| `pipeline` | 多步骤流程 / 数据处理 | pipeline、workflow |
| `concept` | 动机 / 直觉 / 问题定义 | concept、motivation |
| `comparison` | A vs B / Before-After | 对比、vs |

### Prompt 工程

**通用学术约束（每个 prompt 必须追加）：**

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

**类型专用前缀：**

- **architecture**: `Create a technical architecture diagram for an academic paper. Layout: clear left-to-right or top-to-bottom data flow. Components: labeled rectangular modules. Connections: clean directional arrows. Group related components with subtle background regions.`
- **pipeline**: `Create a horizontal step-by-step pipeline diagram. Each stage is a rounded rectangle with concise label. Stages connected by clean arrows. Use subtle color coding for phases.`
- **concept**: `Create a minimal conceptual illustration. Use simple abstract geometric shapes. Maximum clarity, minimum detail. Focus on the core insight.`
- **comparison**: `Create a side-by-side comparison diagram. Clear visual separation between panels. Consistent encoding, highlight key differences.`

**文字处理策略：**

1. 先尝试带文字：在 prompt 中列出所有标签及位置
2. 若文字渲染失败（乱码/拼错），切换无文字模式：`IMPORTANT: Do NOT render any text inside the image. Leave clean blank spaces.` 后期手动叠加

### 配图工作流

```bash
# 定位 gemini-image-gen 引擎
GEMINI_SCRIPT=$(find ~/.agents/skills/gemini-image-gen -name generate_image.py 2>/dev/null | head -1)
```

**Step 1 — 1K 草稿**
```bash
uv run $GEMINI_SCRIPT \
  --prompt "<type prefix + content + labels + academic constraints>" \
  --filename "figures/draft.png" --resolution 1K
```

**Step 2 — visual-checker 审查（最多 3 轮）**

```text
spawn agent=visual-checker task="Check the image at: figures/draft.png
Scene: academic
Intent: <what this figure should show>
Additional context:
- Figure type: <architecture|pipeline|concept|comparison>
- Required labels: <list>"
```

- ✅ PASS → Step 3
- ❌ REGENERATE → 用 `--input-image` 修复后再检查
- 3 轮未通过 → 保存最佳版本，建议手动微调

**Step 3 — 4K 终稿**
```bash
uv run $GEMINI_SCRIPT \
  --prompt "<same prompt>" \
  --filename "figures/final.png" --resolution 4K
```

**Step 4 — LaTeX snippet**

```latex
% 双栏（architecture / pipeline）
\begin{figure*}[t]
    \centering
    \includegraphics[width=0.95\textwidth]{figures/final.png}
    \caption{Self-contained caption. 不读正文也能理解。}
    \label{fig:method}
\end{figure*}

% 单栏（concept / comparison）
\begin{figure}[t]
    \centering
    \includegraphics[width=0.48\textwidth]{figures/final.png}
    \caption{Caption.}
    \label{fig:concept}
\end{figure}
```

### 配图已知限制

1. 文字渲染不稳定（复杂标注建议后期叠加）
2. 几何精度有限（对齐、等距难精确）
3. 跨图风格一致性需用 `--input-image` 参考前图
4. 不适用于数据图表

---

## Phase 4: 格式检查（format-check 子模块）

投稿前/camera-ready 的自动化格式检查。

### 使用前提

- PDF 文件路径
- 目标会议 + 年份
- 论文类型（投稿版 / camera-ready）

### 检查流程

**Step 1 — 元数据检查：**

```bash
# 页数
pdfinfo paper.pdf | grep "Pages"

# 纸张尺寸（US Letter: 612 × 792 pts）
pdfinfo paper.pdf | grep "Page size"

# 字体嵌入（camera-ready 必须全部 yes）
pdffonts paper.pdf | grep -v "yes" | grep -v "^name"

# PDF 元数据作者（双盲不能有）
pdfinfo paper.pdf | grep -i "Author"
```

**Step 2 — 匿名性检查（双盲投稿版）：**

```bash
pdftotext paper.pdf /tmp/paper-text.txt
grep -inE "our (previous|prior|earlier) (work|paper|study)" /tmp/paper-text.txt
grep -inE "university of|institute of|laboratory" /tmp/paper-text.txt
grep -inE "funded by|grant|support.*from" /tmp/paper-text.txt
grep -inE "available at https?://" /tmp/paper-text.txt
```

**Step 3 — 编译日志检查：**

```bash
grep "^!" *.log                              # 致命错误（必须为 0）
grep -cE "Overfull|Underfull" *.log          # 溢出警告
grep "Citation.*undefined" *.log             # 未定义引用（必须为 0）
grep "multiply defined" *.log                # 重复 label
```

**Step 4 — 结构完整性：**

| 章节 | NeurIPS | ICML | ICLR | ACL/ARR | AAAI |
|------|---------|------|------|---------|------|
| Abstract | ✅ | ✅ | ✅ | ✅ | ✅ |
| Limitations | — | — | — | **必需** | — |
| Ethics/Broader Impact | 推荐 | **必需** | — | 推荐 | — |
| NLP Checklist | — | — | — | **必需** | — |

**Step 5 — 引用检查：**

```bash
grep -c "\[?\]" /tmp/paper-text.txt          # [?] 未解析引用
```

- 引用风格一致性（编号 vs 作者-年份）
- 自引比例是否合理

**Step 6 — 视觉审查（可选，用户要求时启用）：**

```bash
mkdir -p /tmp/paper-review
pdftoppm -jpeg -jpegopt quality=85 -r 150 paper.pdf /tmp/paper-review/page
```

为每页调用 `visual-checker`：

```text
spawn agent=visual-checker task="Check the image at: /tmp/paper-review/page-01.jpg
Scene: academic
Intent: Page N of a <conference> paper
Additional context:
- Check for: margin overflow, figure/table readability, label overlap,
  caption placement, column alignment, font size, grayscale distinguishability"
```

### 输出报告模板

```markdown
# 论文格式检查报告

**目标会议**: [会议名]  **论文类型**: [投稿版/camera-ready]  **日期**: [date]

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 页数 | ✅/❌ | X 页（限制 Y） |
| 纸张尺寸 | ✅/❌ | |
| 字体嵌入 | ✅/❌ | |
| 匿名性 | ✅/⚠️/❌ | |
| 编译警告 | ✅/⚠️ | |
| 未定义引用 | ✅/❌ | |
| Limitations | ✅/❌ | |
| Ethics | ✅/⚠️ | |
| 视觉审查 | ✅/⚠️ | |

## ❌ 必须修复（desk reject 风险）
## ⚠️ 建议修复
## ✅ 已通过
```

### 会议格式详表

详见 [references/conference-rules.md](references/conference-rules.md)。

---

## Phase 5: 终审

### 5.1 自查清单

- [ ] Abstract 与 Introduction 的贡献点一致
- [ ] 所有 Figure/Table 在正文中被引用
- [ ] 所有缩写首次出现时展开
- [ ] 数字精度一致（如都保留两位小数）
- [ ] 参考文献格式统一，无重复条目
- [ ] camera-ready：作者信息完整，去掉行号
- [ ] camera-ready：补充 Acknowledgements

### 5.2 语言润色

- 避免 "very" "really" "obviously" 等弱修饰
- 避免第一人称过度使用（"We" 开头不超过 30% 的句子）
- 用主动语态描述 contribution，被动语态描述 related work
- 检查 "which" vs "that"，"less" vs "fewer"

---

## Phase 6: 投稿

### 6.1 Push 到 Overleaf

```bash
# overleaf: push with commit message
git add -A && git commit -m "final submission version" && git push
```

### 6.2 编译 & 下载 PDF

```bash
# overleaf: compile and download
```

### 6.3 提交前最后检查

- PDF 文件大小是否合理（< 50MB）
- Supplementary material 是否需要单独上传
- 匿名 GitHub repo / anonymous.4open.science 是否已准备
- Author response 模板是否已准备（部分会议需要）

---

## 重要提醒

- **不同年份规则可能变化** — 如果用户指定的年份与本 skill 记录的不同，先去官网确认最新 CFP
- **ACL/ARR 的 Limitations 章节缺失 = desk reject**
- **ICML 的 Impact Statement 强烈推荐**
- **AAAI 参考文献计入页数**（唯一例外）
- **ICLR 2025 新增 6 页下限**
- 页数计算方式各会不同，务必按目标会议规则判断
