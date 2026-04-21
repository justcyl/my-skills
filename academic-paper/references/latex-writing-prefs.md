---
# LaTeX 写作偏好（注入用）

写作前注入 agent 的轻量提醒。保持简洁 — 这不是完整规范，是核心偏好的快速备忘。
写完后用 linter 和 review checklist 检查。

---

## 引用

- 作者入句：`\citet{key}`；括号引用：`\citep{key}`；**不要手写** `[1]` 或 `(Author, Year)`
- `\ref` / `\eqref` 前必须有 `~`（non-breaking space）：`Figure~\ref{fig:x}`、`Eq.~\eqref{eq:x}`
- Equation 用 `\eqref`（自带括号）；其他所有交叉引用用 `\ref`

## 公式环境

- 独立公式：`equation` / `align`；不编号：加 `*` 或用 `\notag`
- **不用** `$$ ... $$`，**不用** `eqnarray`
- 只给被引用的公式加 `\label{eq:xxx}`
- 公式是句子一部分时，末尾必须加标点（逗号或句号）：
  ```latex
  % ✅ 正确
  The loss is given by
  \begin{equation}
    \mathcal{L} = -\log p(y \mid x),  % 逗号：公式后继续句子
  \end{equation}
  where $p$ is the output probability.

  % ✅ 句子结束
  We minimize the following objective.
  \begin{equation}
    \mathcal{L} = -\log p(y \mid x).  % 句号
  \end{equation}
  ```
- display math 后继续正文时用 `\noindent` 避免首行缩进：
  ```latex
  \begin{equation}
    f(x) = x^2.
  \end{equation}
  \noindent Here $f$ represents ...   % 不缩进、自然连接
  ```

## 数学符号

- 定义：`:=`（不用 `=` 或 `\triangleq`）
- Transpose：`x^\top`（不用 `x^T`，`T` 留给 iteration horizon）
- Norm：`\|x\|`（不用键盘 `||x||`）
- Log 幂次移外：`d \log a`，不写 `\log(a^d)`
- Big-O 内不放常数：`O(d \log n)`，不写 `O(16d \log n)`
- 多字母下标：`$\mathcal{L}_{\text{ce}}$`，不写 `$L_{ce}$`
- 条件概率：`p(y \mid x)`，不写 `p(y|x)`

## Label

- 三字母前缀 + 冒号：`eq:` `lem:` `thm:` `fig:` `tab:` `sec:` `alg:` `def:` `cor:` `fac:`
- 全小写 + 下划线：`lem:cauchy_schwarz`
- `[display name]` 写在 `\label{}` **之前**：`\begin{lemma}[Name]\label{lem:name}`

## 表格 / 图片

- 表格：用 `booktabs`（`\toprule` / `\midrule` / `\bottomrule`）；caption **在上方**
- 图片：caption **在下方**；内容 self-contained（不读正文也能理解）
- 每个 figure / table 必须在正文中用 `\ref` 引用

## 证明

- 步骤之间加空行
- 每步只写一个 reason；不用 `clearly` / `obviously` 掩盖未说明的步骤

## 排版细节

| 错误 | 正确 |
|------|------|
| `1-10` | `1--10`（en-dash 表范围）|
| `word -- word`（句中）| `word---word`（em-dash）|
| `...` | `\ldots` / `\dots` |
| `"word"` | `` ``word'' `` |
| `50%` | `50\%` |
| `90°` | `$90^{\circ}$` |
