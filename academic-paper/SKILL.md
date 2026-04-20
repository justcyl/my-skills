---
name: academic-paper
description: >
  AI 学术论文全周期写作。覆盖获取模板、Overleaf 项目创建、结构化写作、配图生成、
  格式检查、投稿前审查。内置论文配图（figure-gen）与格式检查（format-check）子模块。
  搭配 overleaf、gemini-image-gen、visual-checker、ph-paper-helper 使用。
  触发语境："写论文""paper writing""投稿前检查""画个架构图""论文配图""格式检查""desk reject"。
---

# Academic Paper

AI 学术论文全周期写作 skill。从获取模板到投稿终审。

## 搭配 Skills

| Skill | 用途 | 何时调用 |
|-------|------|---------|
| **overleaf** | 创建项目 / git clone-push / 编译 / 下载 PDF / review 评论 | 项目初始化及全程同步 |
| **gemini-image-gen** | Gemini 图片生成引擎（text-to-image / image-to-image / 多分辨率） | 配图子模块的底层引擎 |
| **visual-checker** | 视觉 QA 子代理（academic / slides / general scene） | 配图审查、格式视觉审查 |
| **ph-paper-helper** | 论文检索 / 导入 / BibTeX 导出与补全（`ph add --bib` / `ph enrich`） | 文献引用处理 |

---

## 准备阶段

### 1. 确认目标会议与模板

在写任何内容之前，必须确认：

1. **目标会议 + 年份**（如 NeurIPS 2025、ACL 2025）
2. **论文类型**（long / short / workshop / position）
3. **页数限制**（见下方速查表）
4. **DDL**

然后去**该会议官网**下载当年官方 LaTeX 模板。不同年份模板不同，不可复用旧版。

> ⚠️ 不要猜模板链接。每年 CFP 页面会更新模板下载地址。直接搜索 `<Conference> <Year> call for papers` 获取最新版。

### 页数速查

| 会议 | 投稿正文 | Camera-ready | 参考文献 | 备注 |
|------|---------|-------------|---------|------|
| NeurIPS | 10 页 | 10 页 | 不计 | 含图表，不含参考文献/附录 |
| ICML | 8 页 | 9 页 | 不计 | 不含参考文献/Impact/附录 |
| ICLR | 6-10 页 | 同投稿 | 不计 | 6 页下限（2025 新增）|
| ACL/ARR Long | 8 页 | 9 页 | 不计 | Limitations **必须有** |
| ACL/ARR Short | 4 页 | 5 页 | 不计 | 同上 |
| AAAI | 7 页 + 2 附加 | 同投稿 | **计入** | 唯一参考文献计入页数 |

会议格式详表见 [references/conference-rules.md](references/conference-rules.md)。

### 2. 创建 Overleaf 项目

确认论文项目名后，通过 overleaf skill 创建项目、克隆到本地：

```
1. overleaf: 创建项目 "<论文名>"
2. 克隆到本地工作目录
3. 将下载的官方模板文件放入项目
4. push 到 Overleaf 确认编译通过
```

### 3. 检查参考文献

检查项目中是否已有 `.bib` 文件：

- **已有 `.bib`** → 使用 ph-paper-helper 的 `ph enrich --bib <file>.bib` 补全不完整的元数据
- **没有 `.bib`** → 创建空 `references.bib`，在全部写作完成后提醒用户补充参考文献。写作过程中遇到需要引用的地方先用 `\cite{TODO-xxx}` 占位

---

## 写作阶段

本 skill 不限定具体的写作顺序、字数分配或段落结构。论文内容由用户主导，agent 辅助执行。

以下是写作过程中需要遵守的 **LaTeX 规范与常见陷阱**。

### 引用规范

```latex
% ✅ 正确
\citet{vaswani2017attention} propose ...     % 作者名在句中
... as shown by \citep{devlin2019bert}.      % 括号引用

% ❌ 错误
[Vaswani et al., 2017] propose ...           % 手写引用
Vaswani et al. (2017) propose ...            % 手写引用
```

- 使用 `natbib`（`\citet` / `\citep`）或 `biblatex`（`\textcite` / `\parencite`），不要手写
- 自引不宜过多（占总引用 < 20% 为宜）
- 所有引用必须在 `.bib` 中有对应条目

### 交叉引用规范

```latex
% ✅ 正确 — 用 ~ 防断行
Figure~\ref{fig:arch}
Table~\ref{tab:results}
Section~\ref{sec:method}
Equation~\eqref{eq:loss}

% ❌ 错误 — 可能在 Figure 和编号之间断行
Figure \ref{fig:arch}
```

- 每个 Figure / Table **必须在正文中被引用**
- 缩写首次使用时展开：Large Language Model (LLM)

### 公式规范

```latex
% ✅ 行内短公式
The loss is $\mathcal{L} = -\log p(y|x)$.

% ✅ 独立编号公式
\begin{equation}
  \mathcal{L}_{\text{total}} = \mathcal{L}_{\text{ce}} + \lambda \mathcal{L}_{\text{kl}}
  \label{eq:total-loss}
\end{equation}

% ✅ 多行对齐
\begin{align}
  p(y|x) &= \frac{p(x|y) p(y)}{p(x)} \label{eq:bayes} \\
  &= \frac{p(x|y) p(y)}{\sum_{y'} p(x|y') p(y')} \label{eq:bayes-expand}
\end{align}

% ❌ 不要用 $$ ... $$，用 equation 或 align
$$ L = -\log p(y|x) $$

% ❌ 不要用 eqnarray（间距有问题）
\begin{eqnarray} ... \end{eqnarray}
```

**公式排版要点：**

- 行内公式用 `$...$`，独立公式用 `equation` / `align`
- 不用 `$$...$$`（不生成编号，间距控制差）
- 不用 `eqnarray`（改用 `align`）
- 多字母变量名用 `\text{}` 或 `\mathrm{}`：`$\mathcal{L}_{\text{ce}}$` 而非 `$L_{ce}$`
- 被引用的公式必须有 `\label`，用 `\eqref` 引用（带括号）
- 不被引用的公式可用 `equation*` 或 `\nonumber`
- 定义符号时保持全文一致，在 Method 首次出现时解释

### 表格规范

```latex
% ✅ 推荐用 booktabs
\begin{table}[t]
  \centering
  \caption{Results on benchmark X. Best in \textbf{bold}, second \underline{underlined}.}
  \label{tab:results}
  \begin{tabular}{lcc}
    \toprule
    Method & BLEU & ROUGE-L \\
    \midrule
    Baseline & 32.1 & 45.3 \\
    Ours     & \textbf{35.7} & \textbf{48.9} \\
    \bottomrule
  \end{tabular}
\end{table}

% ❌ 不推荐
\begin{tabular}{|l|c|c|}
\hline
Method & BLEU & ROUGE-L \\
\hline
\end{tabular}
```

**表格排版要点：**

- 用 `booktabs`（`\toprule` / `\midrule` / `\bottomrule`），不用 `\hline` + `|`
- 表格 caption 在**上方**（`\caption` 在 `\begin{tabular}` 之前）
- 图片 caption 在**下方**
- 最佳结果加粗（`\textbf{}`），次优下划线（`\underline{}`）
- 数字对齐小数点，保留位数统一
- 大表格用 `\resizebox{\columnwidth}{!}{...}` 或 `\small` 缩放

### 图片规范

```latex
% ✅ 双栏图（architecture / pipeline）
\begin{figure*}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{figures/method.png}
  \caption{Overview of our method. Self-contained caption.}
  \label{fig:method}
\end{figure*}

% ✅ 单栏图
\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{figures/concept.png}
  \caption{Caption.}
  \label{fig:concept}
\end{figure}

% ✅ 子图
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\columnwidth}
    \includegraphics[width=\textwidth]{figures/a.png}
    \caption{Case A}
  \end{subfigure}
  \hfill
  \begin{subfigure}[b]{0.48\columnwidth}
    \includegraphics[width=\textwidth]{figures/b.png}
    \caption{Case B}
  \end{subfigure}
  \caption{Comparison between Case A and Case B.}
  \label{fig:comparison}
\end{figure}
```

**图片排版要点：**

- Caption 必须 self-contained（不读正文也能理解）
- Caption 描述"图里有什么 + 关键发现"，不只是标题
- 使用矢量图（PDF）或高分辨率 PNG（≥ 300 DPI）
- 图中文字不小于正文字号的 80%
- 灰度打印时仍可区分不同曲线/区域

### 常见 LaTeX 不规范清单

| 问题 | 错误写法 | 正确写法 |
|------|---------|---------|
| 手写引用 | `[1]`、`(Vaswani et al., 2017)` | `\citep{vaswani2017}` |
| 断行风险 | `Figure \ref{fig:x}` | `Figure~\ref{fig:x}` |
| 独立公式 | `$$ ... $$` | `\begin{equation} ... \end{equation}` |
| 多行公式 | `eqnarray` | `align` |
| 表格线 | `\|l\|c\|` + `\hline` | `booktabs` 三线表 |
| 表格 caption 位置 | caption 在表格下方 | caption 在表格上方 |
| 下划线强调 | `\underline{text}` 在正文 | `\emph{text}` 或 `\textit{}` |
| 连字符误用 | `state of the art` | `state-of-the-art`（形容词）|
| 数字范围 | `1-10` | `1--10`（en-dash）|
| 破折号 | `--` 在句中 | `---`（em-dash）或重写句子 |
| 省略号 | `...` | `\ldots` 或 `\dots` |
| 引号 | `"word"` | `` ``word'' `` |
| 百分号 | `50%` | `50\%` |
| 角度/度 | `90°` | `$90^{\circ}$` |
| 数学变量 | `the loss L` | `the loss $L$` |
| 多字母变量 | `$BLEU$` | `$\text{BLEU}$` 或 `\textsc{Bleu}` |
| 条件概率 | `$p(y|x)$` | `$p(y \mid x)$`（间距更好）|
| 集合 | `$\{1,2,3\}$` | `$\{1, 2, 3\}$`（逗号后空格）|
| 约等于 | `$\approx$` 和 `$\sim$` 混用 | 全文统一使用一种 |
| e.g. / i.e. | `eg.` / `ie.` | `e.g.,\` / `i.e.,\` 或 `\eg` |
| et al. | `et al` / `Et al.` | `et al.`（带点，不斜体）|

### 算法伪代码规范

```latex
\usepackage{algorithm}
\usepackage{algorithmic}  % 或 algpseudocode

\begin{algorithm}[t]
  \caption{Our Training Procedure}
  \label{alg:train}
  \begin{algorithmic}[1]
    \REQUIRE Dataset $\mathcal{D}$, learning rate $\eta$
    \ENSURE Trained model $\theta^*$
    \STATE Initialize $\theta$ randomly
    \FOR{epoch $= 1$ \TO $T$}
      \FOR{batch $(x, y) \in \mathcal{D}$}
        \STATE $\mathcal{L} \leftarrow \text{Loss}(f_\theta(x), y)$
        \STATE $\theta \leftarrow \theta - \eta \nabla_\theta \mathcal{L}$
      \ENDFOR
    \ENDFOR
    \RETURN $\theta^* = \theta$
  \end{algorithmic}
\end{algorithm}
```

---

## 配图生成（figure-gen 子模块）

为学术论文生成 publication-quality 概念图：架构图、pipeline、概念图、对比图。

> 数据驱动图表（bar chart / line plot / heatmap）不属于本模块，用 matplotlib/seaborn 直接绘制。

### 配图类型

| 类型 | 用途 | 关键词 |
|------|------|--------|
| `architecture` | Method Overview / Figure 1 | 架构图、framework |
| `pipeline` | 多步骤流程 | pipeline、workflow |
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
- Professional and restrained — this is for a top-tier academic paper, not a poster
```

**类型专用前缀：**

- **architecture**: `Create a technical architecture diagram for an academic paper. Layout: clear left-to-right or top-to-bottom data flow. Components: labeled rectangular modules. Connections: clean directional arrows. Group related components with subtle background regions.`
- **pipeline**: `Create a horizontal step-by-step pipeline diagram. Each stage: rounded rectangle with concise label. Stages connected by clean arrows. Subtle color coding for phases.`
- **concept**: `Create a minimal conceptual illustration. Simple abstract geometric shapes. Maximum clarity, minimum detail. Focus on the core insight.`
- **comparison**: `Create a side-by-side comparison diagram. Clear visual separation between panels. Consistent encoding, highlight key differences.`

**文字处理策略：**

1. 先尝试带文字 — 在 prompt 中列出所有标签及位置
2. 若文字渲染失败（乱码/拼错）→ 切换无文字模式：`Do NOT render any text. Leave blank spaces.` 后期手动叠加

### 配图工作流

使用 gemini-image-gen skill 的 `generate_image.py` 脚本作为生图引擎。

**Step 1 — 1K 草稿生成**

使用 `--resolution 1K` 快速出稿。

**Step 2 — visual-checker 审查（最多 3 轮）**

生成后调用 visual-checker（scene: `academic`）做自动视觉审查：

- ✅ PASS → 进入 Step 3
- ⚠️ MINOR → 可选修复
- ❌ REGENERATE → 根据 Regeneration Guidance 用 `--input-image` 编辑修复后再次检查

3 轮未通过 → 保存最佳版本，告知用户具体不足，建议 draw.io / Figma / TikZ 手动微调。

**Step 3 — 4K 终稿**

确认后使用 `--resolution 4K` 生成高分辨率终稿。

### 配图已知限制

- 文字渲染不稳定（复杂标注建议后期叠加）
- 几何精度有限（对齐、等距难精确）
- 跨图风格一致性需用 `--input-image` 参考前图
- 不适用于数据驱动图表

---

## 格式检查（format-check 子模块）

投稿前 / camera-ready 的自动化格式检查。

### 需要用户提供

- PDF 文件路径
- 目标会议 + 年份
- 论文类型（投稿版 / camera-ready）

### 自动化检查

**元数据检查：**

```bash
pdfinfo paper.pdf | grep "Pages"          # 页数
pdfinfo paper.pdf | grep "Page size"      # 纸张（US Letter: 612 × 792 pts）
pdffonts paper.pdf | grep -v "yes"        # 字体嵌入（camera-ready 全部 yes）
pdfinfo paper.pdf | grep -i "Author"      # 双盲不能有作者
```

**匿名性检查（双盲投稿版）：**

```bash
pdftotext paper.pdf /tmp/paper-text.txt
grep -inE "our (previous|prior|earlier) (work|paper|study)" /tmp/paper-text.txt
grep -inE "university of|institute of|laboratory" /tmp/paper-text.txt
grep -inE "funded by|grant|support.*from" /tmp/paper-text.txt
grep -inE "available at https?://" /tmp/paper-text.txt
```

**编译日志检查：**

```bash
grep "^!" *.log                            # 致命错误（必须为 0）
grep -cE "Overfull|Underfull" *.log        # 溢出警告
grep "Citation.*undefined" *.log           # 未定义引用（必须为 0）
grep "multiply defined" *.log              # 重复 label
```

**结构完整性：**

| 章节 | NeurIPS | ICML | ICLR | ACL/ARR | AAAI |
|------|---------|------|------|---------|------|
| Abstract | ✅ | ✅ | ✅ | ✅ | ✅ |
| Limitations | — | — | — | **必需** | — |
| Ethics/Impact | 推荐 | **推荐** | — | 推荐 | — |
| NLP Checklist | — | — | — | **必需** | — |

**引用检查：**

```bash
grep -c "\[?\]" /tmp/paper-text.txt        # [?] 未解析引用
```

### 视觉审查（可选，用户要求时启用）

将 PDF 转为页面图片后，逐页使用 visual-checker（scene: `academic`）审查：

```bash
mkdir -p /tmp/paper-review
pdftoppm -jpeg -jpegopt quality=85 -r 150 paper.pdf /tmp/paper-review/page
```

检查项包括：边距溢出、图表可读性、label 重叠、caption 位置、双栏对齐、字号一致性、灰度可辨识、首页作者信息。

### 输出报告

```markdown
# 格式检查报告

**会议**: [name]  **类型**: [投稿/camera-ready]  **日期**: [date]

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 页数 | ✅/❌ | |
| 纸张尺寸 | ✅/❌ | |
| 字体嵌入 | ✅/❌ | |
| 匿名性 | ✅/⚠️/❌ | |
| 编译警告 | ✅/⚠️ | |
| 未定义引用 | ✅/❌ | |
| 必需章节 | ✅/❌ | |
| 视觉审查 | ✅/⚠️ | |

## ❌ 必须修复（desk reject 风险）
## ⚠️ 建议修复
## ✅ 已通过
```

---

## 投稿前自查清单

- [ ] 所有 `\cite{TODO-xxx}` 占位已替换为真实引用
- [ ] Abstract 与 Introduction 末尾的贡献点一致
- [ ] 每个 Figure / Table 在正文中被 `\ref` 引用
- [ ] 每个编号公式在正文中被 `\eqref` 引用
- [ ] 缩写首次出现时展开
- [ ] 数字精度统一（如都保留两位小数）
- [ ] 参考文献无重复条目、格式统一
- [ ] `.bib` 中所有条目元数据完整（用 `ph enrich --bib` 检查）
- [ ] 没有 `[?]` 未解析引用
- [ ] 没有 `Overfull \hbox` 超过 1pt 的警告
- [ ] Camera-ready：作者信息完整、去掉行号、补充 Acknowledgements
- [ ] 投稿版：无作者信息、有行号
- [ ] ACL/ARR：Limitations 章节存在、Responsible NLP Checklist 已填
- [ ] PDF < 50MB
- [ ] 匿名 code repo（如 anonymous.4open.science）已准备（如需要）

---

## 重要提醒

- **不同年份规则可能变化** — 始终去官网确认当年 CFP
- **ACL/ARR 的 Limitations 章节缺失 = desk reject**
- **AAAI 参考文献计入页数**（唯一例外）
- **ICLR 2025 新增 6 页下限**
- 页数计算方式各会不同，务必按目标会议规则判断
