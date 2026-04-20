---
name: latex-lint
description: 基于「打字抄能力」系列的 LaTeX 学术写作规范检查。当用户请求检查 LaTeX 源码规范、论文排版质量、proof 写作风格时触发。内置 linter 脚本自动检测常见问题（label 命名、引用格式、proof 换行、bracket sizing、BibTeX key 等），并提供修复建议。适用于："帮我检查 LaTeX""论文格式检查""lint my tex""proof 写法有没有问题""检查一下 overleaf 项目"。
---

# LaTeX Lint — 学术 LaTeX 写作规范检查

基于 B 站 @simapofang「打字抄能力」系列提炼的 LaTeX 学术写作规范。
核心理念：**先用脚本自动扫描，再人工审阅脚本无法覆盖的语义问题**。

## 快速开始

收到用户的 LaTeX 检查请求后：

1. 确定要检查的 `.tex` / `.bib` 文件路径
2. 运行 linter 脚本：
   ```bash
   python3 <skill-dir>/scripts/latex_lint.py <file-or-directory> [--bib] [--fix-preview]
   ```
3. 阅读 linter 输出，按严重程度排序向用户汇报
4. 对 linter 无法覆盖的语义问题（如 proof 逻辑拆分、roadmap 一致性），进行人工审阅
5. 给出具体修复建议和示例代码

## 规范总览

以下规范按类别组织。每条规范标注 `[AUTO]`（脚本可检测）或 `[MANUAL]`（需人工审阅）。

### 1. Label 命名

- `[AUTO]` Label 使用三字母前缀 + 冒号：`thm:`, `lem:`, `cor:`, `def:`, `fac:`, `sec:`, `eq:`, `fig:`, `tab:`, `alg:`, `app:`, `rem:`
- `[AUTO]` Label 名全小写，用下划线分隔单词：`lem:cauchy_schwarz` ✓，`Lem:Cauchy-Schwarz` ✗
- `[AUTO]` 不要用减号或空格：`lem:cauchy-schwarz` ✗
- `[MANUAL]` Label 名应有意义，用一两个英文单词概括内容——不要用 `eq:1`, `lem:a` 这种无意义编号
- `[AUTO]` 对于 main tex + appendix 双版本，main 用 `:informal` 后缀，appendix 用 `:formal` 后缀
- `[AUTO]` `\label` 和 `[display name]` 的顺序不能交换——`\label` 必须在 `[...]` 之后

### 2. 引用格式

- `[AUTO]` Theorem/Lemma 引用：`Lemma~\ref{lem:xxx}` — 波浪线 `~` 产生不换行空格
- `[AUTO]` Equation 引用：`Eq.~\eqref{eq:xxx}` — 不要写完整的 `Equation`，不要用 `\ref` 引用 equation
- `[AUTO]` 引用 equation 时用 `\eqref`（自带括号），引用 theorem 等用 `\ref`（不带括号）
- `[AUTO]` 不要在非 equation 环境上使用 `\eqref`

### 3. Equation 环境

- `[AUTO]` 未被引用的 equation 使用 star 环境（`equation*`, `align*`）或 `\notag`
- `[AUTO]` 不要在 star 环境中放 `\label` — 会产生 warning
- `[AUTO]` 使用 `\notag` 而非 `\nonumber`（二者等价，但统一用 `\notag`）
- `[AUTO]` Equation label 前缀用 `eq:` 不要写全称 `equation:`

### 4. 括号与分数

- `[AUTO]` 不要自行使用 `\big`, `\Big`, `\bigg`, `\Bigg` 调整括号大小——保持默认大小，留给 advisor 统一调整
- `[AUTO]` 不要过度使用 `\left`/`\right`——只在确实需要自动缩放时使用
- `[MANUAL]` 分数：当分子分母都很短时用 `\frac{a}{b}`；当分子很长分母很短（或反之）时考虑用 inline 形式 `a/b`，避免排版失衡

### 5. 数学符号与定义

- `[AUTO]` 定义新符号用 `:=`（冒号等号），不要用 `=` 或 `\triangleq`
- `[AUTO]` 概率用 `\Pr`（或自定义 `\Pr` 命令），期望用 `\E`（需自定义）
- `[MANUAL]` 向量用 `\begin{bmatrix}...\end{bmatrix}`（方括号矩阵），不要用 `\begin{pmatrix}`（圆括号）
- `[AUTO]` 对数中的幂次应提取出来：`\log(a^d)` 应写成 `d \log(a)`
- `[MANUAL]` 每个使用的 named inequality / theorem 必须有 citation（Markov, Chebyshev, Hoeffding, Jensen 等）

### 6. Proof 写作风格

- `[AUTO]` Proof 中每个 equation 后应换行再写原因——不要把 "where ... " 紧接在 equation 后面同一行
- `[MANUAL]` 每一步推导只写一个原因；如果某一步需要多个原因，应拆成多步
- `[MANUAL]` 写 long equation 链时，展示中间步骤——不要从 A 直接跳到 E，应该写 A ≤ B ≤ C ≤ D ≤ E
- `[MANUAL]` Proof 应 self-contained：所有用到的符号都要有定义或引用
- `[MANUAL]` 防御性写证明：概率常数用整数分母（1/10 而非 1/4），给未来修改留余地
- `[MANUAL]` 不要在 `\log` 里写 power——所有 power 都移到外面

### 7. BibTeX

- `[AUTO]` BibTeX key 格式：`lastname + year`（如 `he2016`），多作者用 last name
- `[AUTO]` 5+ 作者的 key 用首字母：`abc2024`
- `[AUTO]` 同年同作者有多篇用字母后缀：`he2016a`, `he2016b`
- `[AUTO]` Key 不要用 first name
- `[MANUAL]` 引用优先级：journal > conference > arXiv
- `[MANUAL]` 始终引用最新版本

### 8. Roadmap

- `[AUTO]` Main body 在 intro 或 related work 后应有 `\paragraph{Roadmap.}` 或类似结构
- `[AUTO]` Appendix 开头应有 roadmap
- `[MANUAL]` Roadmap 中引用的 section/theorem 编号必须与实际一致
- `[MANUAL]` 每次修改论文结构后，检查所有 roadmap 是否需要更新

### 9. 源码可读性

- `[AUTO]` 证明步骤之间应有空行分隔
- `[MANUAL]` TeX 源码本身应可读——不依赖 PDF 也能理解结构（"我一般写 LaTeX 的时候，我是不看 PDF，直接看 TeX"）
- `[MANUAL]` 长证明要拆短，多换行
- `[MANUAL]` Equation 后补充原因时，尽量用英文写出 reasoning text

### 10. Overleaf 协作

- `[MANUAL]` 使用 name tag 标记待完成任务
- `[MANUAL]` 使用 comments 进行异步交流，完成后 resolve
- `[MANUAL]` 不要修改 advisor 调整过的 bracket sizing
- `[MANUAL]` 抄别人论文的公式时，要按自己组的 notation 体系重新调整

## Linter 脚本用法

```bash
# 检查单个文件
python3 <skill-dir>/scripts/latex_lint.py paper.tex

# 检查整个目录
python3 <skill-dir>/scripts/latex_lint.py ./my-paper/

# 同时检查 .bib 文件
python3 <skill-dir>/scripts/latex_lint.py ./my-paper/ --bib

# 预览修复建议
python3 <skill-dir>/scripts/latex_lint.py paper.tex --fix-preview

# 输出 JSON 格式（便于程序处理）
python3 <skill-dir>/scripts/latex_lint.py paper.tex --json
```

### Linter 输出格式

```
[ERROR] paper.tex:42 — label 使用了减号: \label{lem:cauchy-schwarz}
  → 修复: \label{lem:cauchy_schwarz}

[WARN]  paper.tex:87 — equation 引用使用了 \ref 而非 \eqref: \ref{eq:main}
  → 修复: Eq.~\eqref{eq:main}

[INFO]  paper.tex:120 — 检测到 \left/\right 括号对, 请确认是否必要
```

严重级别：
- `ERROR`: 明确违反规范，应当修复
- `WARN`: 可能违反规范，建议检查
- `INFO`: 风格建议，非强制

## 人工审阅清单

Linter 之后，逐项人工检查以下 `[MANUAL]` 项目：

1. **Label 语义**：是否有无意义的编号式 label？
2. **分数排版**：长分子短分母的 `\frac` 是否应改为 inline？
3. **Proof 逻辑**：每步是否只有一个原因？是否有跳步？
4. **符号 citation**：每个 named inequality 是否都有 citation？
5. **Roadmap 一致性**：roadmap 中的引用是否与实际对应？
6. **防御性常数**：概率 union bound 的常数是否留有余地？
7. **向量矩阵**：是否统一使用 bmatrix（方括号）？
8. **BibTeX 版本**：是否引用了最新版本？是否优先 journal？
9. **源码可读性**：TeX 源码不看 PDF 能否理解？
10. **Notation 一致性**：合并多篇论文 notation 时是否统一？

## 输出格式

向用户呈现检查结果时，使用以下结构：

```
## 🔍 LaTeX Lint 检查结果

### 自动检测（N 个问题）

| 级别 | 文件:行 | 问题描述 | 修复建议 |
|------|---------|----------|----------|
| ERROR | ... | ... | ... |

### 人工审阅发现（M 个建议）

1. **[类别]** 具体问题描述 + 修复建议
```

## 适用范围与限制

- 适用于学术论文（特别是理论方向 CS/ML 论文）
- 规范来自特定课题组的实践总结，不代表所有学术社区的共识
- 部分规范（如 bmatrix vs pmatrix）取决于领域传统，应以目标会议/期刊的 style guide 为准
- Linter 基于正则匹配，可能产生 false positive——始终结合上下文判断
