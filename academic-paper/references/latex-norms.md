# LaTeX 规范（完整参考）

> **使用定位**：本文件是完整规范库（查阅用）。
> 操作时请使用对应的小文件：
> - **写前**：[latex-writing-prefs.md](latex-writing-prefs.md)
> - **写完后 lint**：`scripts/latex_lint.py` / `scripts/check_hard_rules.sh`
> - **写完后 review**：[latex-review-checklist.md](latex-review-checklist.md)

每条规范标注 `[AUTO]`（linter 可检测）或 `[MANUAL]`（需人工审阅）。

---

## 快速上手:Linter 脚本

每条规范标注 `[AUTO]`(脚本可检测)或 `[MANUAL]`(需人工审阅)。

```bash
# 检查单个文件
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py paper.tex

# 检查整个目录(自动递归 .tex)
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py ./my-paper/ --bib

# 预览修复建议
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py paper.tex --fix-preview

# 只显示 ERROR 和 WARN
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py paper.tex --severity WARN

# JSON 输出(方便程序消费)
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py paper.tex --json
```

严重级别:`ERROR`(应当修复)/ `WARN`(建议检查)/ `INFO`(风格建议)

---

## 1. Label 命名

- `[AUTO]` 使用三字母前缀 + 冒号:`thm:`, `lem:`, `cor:`, `def:`, `fac:`, `sec:`, `eq:`, `fig:`, `tab:`, `alg:`, `app:`, `rem:`, `prop:`, `ass:`, `cla:`
- `[AUTO]` Label 名全小写,下划线分隔:`lem:cauchy_schwarz` ✓,`Lem:Cauchy-Schwarz` ✗
- `[AUTO]` 不用减号或空格
- `[MANUAL]` Label 名要有语义,用 1-2 个英文单词概括内容,不要用 `eq:1`、`lem:a`
- `[AUTO]` Main body 版本用 `_informal` 后缀,Appendix formal 版本用 `_formal` 后缀
- `[AUTO]` `\label` 必须在 `[display name]` **之后**,顺序颠倒会产生 bug:

```latex
% ✅ 正确
\begin{lemma}[Cauchy--Schwarz]\label{lem:cauchy_schwarz}

% ❌ 错误
\begin{lemma}\label{lem:cauchy_schwarz}[Cauchy--Schwarz]
```

- `[AUTO]` Equation label 前缀用 `eq:`,不要写全称 `equation:`

---

## 2. 引用与交叉引用

- `[AUTO]` Equation 引用:`Eq.~\eqref{eq:xxx}`--不写全称 `Equation`,不用 `\ref`
- `[AUTO]` Theorem / Lemma / Definition / Section / Figure / Table 引用:`Lemma~\ref{lem:xxx}`
- `[AUTO]` `\ref` 不带括号,`\eqref` 自带括号--不要在 equation 上用 `\ref`,不要在非 equation 上用 `\eqref`
- `[AUTO]` 引用前必须有 `~`(non-breaking space,防断行)

```latex
% ✅ 正确
as shown in Figure~\ref{fig:arch},
see Eq.~\eqref{eq:loss},
by Lemma~\ref{lem:key}.

% ❌ 错误(断行风险 / 括号错用)
Figure \ref{fig:arch}
Eq.~\ref{eq:loss}       % 缺括号
```

- `[AUTO]` 每个 Figure / Table **必须在正文中被引用**
- 缩写首次使用时展开:Large Language Model (LLM)

---

## 3. Equation 环境

- `[AUTO]` 不用 `$$ ... $$`(无编号,间距差),改用 `equation` 或 `equation*`
- `[AUTO]` 不用 `eqnarray`(间距有 bug),改用 `align` / `align*`
- `[AUTO]` 未被引用的 equation 使用 star 环境(`equation*` / `align*`)或 `\notag`
- `[AUTO]` 不在 star 环境中放 `\label`(冲突产生 warning)
- `[AUTO]` 统一用 `\notag`,不用 `\nonumber`
- `[AUTO]` 被引用的公式必须有 `\label{eq:xxx}`,用 `\eqref` 引用

```latex
% ✅ 独立编号公式
\begin{equation}
  \mathcal{L} = -\log p(y \mid x)
  \label{eq:loss}
\end{equation}

% ✅ 多行对齐
\begin{align}
  p(y \mid x) &\le B_1  \label{eq:step1} \\
              &\le B_2  \label{eq:step2}
\end{align}

% ✅ 不需要编号
\begin{equation*}
  Z = \sum_{y} \exp(f(x,y))
\end{equation*}

% ❌
$$ L = ... $$
\begin{eqnarray} ... \end{eqnarray}
```

---

## 4. 括号与分数

- `[AUTO]` 不要自行使用 `\big`, `\Big`, `\bigg`, `\Bigg`--保持默认大小,留给 advisor 统一调整
- `[AUTO]` 不要过度使用 `\left`/`\right`--初学者不应随意调整 bracket size
- `[MANUAL]` Display equation 中复杂分式用 `\frac`;inline 中简单分数用 `1/2`(比 `\frac{1}{2}` 紧凑)
- `[MANUAL]` 分子分母不对称(长分子短分母)考虑改写为 inline 形式避免排版失衡

---

## 5. 数学符号与定义

- `[AUTO]` 定义新符号用 `:=`,不用 `=` 或 `\triangleq`
- `[AUTO]` Transpose 用 `\top`(`x^\top`),不用 `^T`--`T` 常表示 iteration horizon,有冲突风险
- `[AUTO]` Norm 用 `\|x\|`,不用键盘 `||x||`;norm 类型需明确($\ell_1$, $\ell_2$, $\ell_\infty$, Frobenius 等)
- `[AUTO]` 对数内幂次移至外:`\log(a^d)` → `d \log(a)`(log 内写 power 是强烈反例)
- `[AUTO]` big-O 内不放无意义常数:`O(16d\log n)` → `O(d\log n)`
- `[AUTO]` 行内多字母变量/函数名用 `\text{}` 或 `\mathrm{}`:`$\mathcal{L}_{\text{ce}}$` 而非 `$L_{ce}$`
- `[AUTO]` 条件概率间距:`$p(y \mid x)$` 而非 `$p(y|x)$`(`\mid` 间距更好)
- `[MANUAL]` 概率用 `\Pr`,期望用项目已有 macro(`\E` 或 `\mathbb{E}`),全文统一
- `[MANUAL]` 向量用方括号矩阵 `\begin{bmatrix}...\end{bmatrix}`,不用 `pmatrix`(圆括号)
- `[MANUAL]` 每个 named inequality / theorem 首次使用必须有 citation(Markov, Chebyshev, Hoeffding, Jensen, Bernstein, Cauchy-Schwarz 等)
- `[MANUAL]` Pseudo-inverse 用 `\dagger` 而非 `^+`(`^+` 打错后难与普通加法区分)
- `[MANUAL]` Inner product 用 `\langle a, b \rangle`;Hadamard product 用 `\odot`;集合条件分隔符(`:` 或 `\mid`)全文统一

```latex
% ✅
f := \lambda x^\top A x       % 定义用 :=
x^\top A x                     % transpose 用 \top
\|x\|_2, \|A\|_F               % norm 用 \|
d \log(a)                       % 幂次移出 log
O(d \log n)                     % big-O 无常数
$\mathcal{L}_{\text{ce}}$       % 多字母下标
$p(y \mid x)$                   % 条件概率
```

---

## 6. Proof 写作

- `[AUTO]` 证明步骤之间应有空行分隔,不要写成一坨
- `[AUTO]` 检测 `clearly` / `obviously` 等掩盖不清楚步骤的词
- `[MANUAL]` 每步推导只写一个原因;需多个原因就拆成多步
- `[MANUAL]` Reason 必须真实--不能写假理由(如 "by abstract value");不确定时留 TODO comment
- `[MANUAL]` 展示中间步骤--不要从 A 直接跳到 E
- `[MANUAL]` Proof 必须 self-contained:所有用到的符号、工具都要有定义或引用
- `[MANUAL]` 防御性写证明:概率常数用整数分母(δ/10 而非 δ/4),top-down 设计失败概率分配,给未来修改留余地
- `[MANUAL]` 常数要么精确写清,要么用 O(·) 隐藏干净--不要两者同时出现

```latex
% ✅ 多步一因,有空行,有原因
\begin{align}
  A &\le B && \text{by Lemma~\ref{lem:first}} \\
    &\le C && \text{by Jensen's inequality \citep{jensen1906}} \\
    &\le D && \text{by a union bound}
\end{align}

% ❌
... clearly we have $A \le D$. % clearly 掩盖了跳步
```

---

## 7. 表格排版

- `[MANUAL]` 使用 `booktabs` 包(`\toprule` / `\midrule` / `\bottomrule`),不用 `\hline` + `|`
- `[MANUAL]` 表格 caption 在**上方**(`\caption` 在 `\begin{tabular}` 之前)
- `[MANUAL]` 最佳结果加粗(`\textbf{}`),次优下划线(`\underline{}`)
- `[MANUAL]` 数字对齐小数点,同列保留位数统一
- `[MANUAL]` 大表格用 `\resizebox{\columnwidth}{!}{...}` 或 `\small` 缩放

```latex
% ✅
\begin{table}[t]
  \centering
  \caption{Results. Best in \textbf{bold}.}\label{tab:results}
  \begin{tabular}{lcc}
    \toprule
    Method & BLEU & ROUGE-L \\
    \midrule
    Baseline & 32.1 & 45.3 \\
    Ours     & \textbf{35.7} & \textbf{48.9} \\
    \bottomrule
  \end{tabular}
\end{table}

% ❌
\begin{tabular}{|l|c|c|}
\hline ...\hline
\end{tabular}
```

---

## 8. 图片排版

- `[MANUAL]` Caption 在图片**下方**,必须 self-contained(不读正文也能理解)
- `[MANUAL]` Caption 描述"图里有什么 + 关键发现/结构",不只是标题
- `[MANUAL]` 使用矢量图(PDF / SVG)或高分辨率 PNG(≥ 300 DPI)
- `[MANUAL]` 图中文字不小于正文字号的 80%;灰度打印时仍可区分不同曲线/区域
- `[MANUAL]` 多子图用 `subfigure`,`\hfill` 填充间距

```latex
% ✅ 双栏图
\begin{figure*}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{figures/method.pdf}
  \caption{Overview. Self-contained description.}
  \label{fig:method}
\end{figure*}

% ✅ 子图
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\columnwidth}
    \includegraphics[width=\textwidth]{figures/a.pdf}
    \caption{Case A.}
  \end{subfigure}\hfill
  \begin{subfigure}[b]{0.48\columnwidth}
    \includegraphics[width=\textwidth]{figures/b.pdf}
    \caption{Case B.}
  \end{subfigure}
  \caption{Comparison.}\label{fig:compare}
\end{figure}
```

---

## 9. 算法伪代码

- `[MANUAL]` 使用 `algorithm` + `algorithmic`(或 `algpseudocode`)包
- `[MANUAL]` 函数名使用 small caps:`\textsc{Encode}`, `\textsc{Sample}`
- `[MANUAL]` `\REQUIRE` / `\ENSURE`(`algorithmic`)或 `\Require` / `\Ensure`(`algpseudocode`),视包而定,全文统一

```latex
\begin{algorithm}[t]
  \caption{Training Procedure}\label{alg:train}
  \begin{algorithmic}[1]
    \REQUIRE Dataset $\mathcal{D}$, learning rate $\eta$
    \ENSURE Trained model $\theta^*$
    \STATE Initialize $\theta$ randomly
    \FOR{epoch $= 1$ \TO $T$}
      \FOR{$(x, y) \in \mathcal{D}$}
        \STATE $\mathcal{L} \gets \text{Loss}(f_\theta(x), y)$
        \STATE $\theta \gets \theta - \eta \nabla_\theta \mathcal{L}$
      \ENDFOR
    \ENDFOR
    \RETURN $\theta^* \gets \theta$
  \end{algorithmic}
\end{algorithm}
```

---

## 10. BibTeX Key

- `[AUTO]` 格式:`lastname + year`,如 `he2016`
- `[AUTO]` 1-4 作者写出 last name;5+ 作者用首字母缩写 + 年份:`abc2024`
- `[AUTO]` 同年同作者多篇用字母后缀:`he2016a`, `he2016b`
- `[AUTO]` Key 不要用 first name
- `[MANUAL]` 引用优先级:journal > conference > arXiv
- `[MANUAL]` 始终引用最新发表版本
- `[MANUAL]` 每个 named inequality / 标准工具首次出现必须有 citation

---

## 11. Roadmap

- `[AUTO]` Main body 在 intro 末尾或 related work 后必须有 `\paragraph{Roadmap.}`
- `[AUTO]` Appendix 开头必须有 roadmap
- `[MANUAL]` Roadmap 引用的 section/theorem 编号与实际一致
- `[MANUAL]` 每次修改论文结构后检查所有 roadmap

```latex
\paragraph{Roadmap.}
The remainder of this paper is organized as follows.
In Section~\ref{sec:prelim}, we introduce notation.
Section~\ref{sec:method} presents our method.
```

---

## 12. Notation 系统设计

- `[MANUAL]` 好的 notation:语义清楚、全文一致、避免冲突、写错后可唯一修回、可扩展、符合领域习惯
- `[MANUAL]` 矩阵维度符号应有语义关系:`X \in \mathbb{R}^{n \times d}, W \in \mathbb{R}^{d \times k}` ✓(而非无语义的 `A \in \mathbb{R}^{u \times c}`)
- `[MANUAL]` `[d] := \{1, \ldots, d\}` 如使用需在 preliminaries 中定义
- `[MANUAL]` 合并多篇论文 notation 时:列出两套系统、确定主系统、逐个迁移(不只是 find-and-replace,要检查维度和含义)、写 notation table

---

## 13. Theorem / Lemma / Definition 职责

- `[MANUAL]` **Definition**:引入概念,不需 proof,定义符号用 `:=`
- `[MANUAL]` **Fact**(`fac:` 前缀):标准事实,需 citation
- `[MANUAL]` **Lemma**:为 theorem 服务的中间结论,需 proof 或 citation
- `[MANUAL]` **Theorem**:主要结论
- `[MANUAL]` **Claim**:比 lemma 更局部,可在 proof 内部使用
- `[MANUAL]` Appendix formal statement 要条件完整,不要写 "Under the same assumptions as before"

```latex
% ✅ Appendix formal statement 模板
\begin{lemma}[Formal version of Lemma~\ref{lem:key_informal}]
\label{lem:key_formal}
Suppose:
\begin{enumerate}
  \item $n \ge C \cdot d \log(1/\delta)$;
  \item $\delta \in (0, 1)$;
  \item Assumption~\ref{ass:lipschitz} holds with constant $L$.
\end{enumerate}
Then ...
\end{lemma}
```

---

## 14. 常见不规范速查表

| 问题 | 错误写法 | 正确写法 |
|------|---------|---------|
| 手写引用 | `[1]`、`(Vaswani et al., 2017)` | `\citep{vaswani2017}` |
| 断行风险 | `Figure \ref{fig:x}` | `Figure~\ref{fig:x}` |
| Equation 引用括号 | `Equation~\ref{eq:x}` | `Eq.~\eqref{eq:x}` |
| 独立公式环境 | `$$ ... $$` | `\begin{equation} ... \end{equation}` |
| 多行公式环境 | `eqnarray` | `align` |
| 不编号公式 | `\nonumber` | `\notag` 或 star 环境 |
| 定义符号 | `f = \lambda x` 或 `f \triangleq \lambda x` | `f := \lambda x` |
| Transpose | `x^T` | `x^\top` |
| Norm | `\|\|x\|\|` 或键盘 `||x||` | `\|x\|` |
| Log 内幂次 | `\log(a^d)` | `d \log(a)` |
| Big-O 常数 | `O(16d\log n)` | `O(d\log n)` |
| 多字母下标 | `$L_{ce}$` | `$\mathcal{L}_{\text{ce}}$` |
| 条件概率间距 | `$p(y|x)$` | `$p(y \mid x)$` |
| 集合括号 | `$\{1,2,3\}$` | `$\{1, 2, 3\}$` |
| Label 位置 | `\begin{lemma}\label{}\[name\]` | `\begin{lemma}[name]\label{}` |
| Label 前缀 | `equation:loss` | `eq:loss` |
| 表格线条 | `\|l\|c\|` + `\hline` | `booktabs` 三线表 |
| 表格 caption 位置 | caption 在表格下方 | caption 在表格上方 |
| 下划线强调正文 | `\underline{text}` | `\emph{text}` |
| 数字范围 | `1-10` | `1--10`(en-dash)|
| 破折号 | `word--word` 句中 | `---`(em-dash)|
| 省略号 | `...` | `\ldots` 或 `\dots` |
| 引号 | `"word"` | `` ``word'' `` |
| 百分号 | `50%` | `50\%` |
| 度数 | `90°` | `$90^{\circ}$` |
| 数学变量 | `the loss L` | `the loss $L$` |
| 多字母变量 | `$BLEU$` | `$\text{BLEU}$` 或 `\textsc{Bleu}` |
| 连字符误用 | `state of the art`(形容词)| `state-of-the-art` |
| e.g. / i.e. | `eg.` / `ie.` | `e.g.,` / `i.e.,` |
| et al. | `et al` / `Et al.` | `et al.` |
| Proof 掩盖跳步 | `clearly` / `obviously` | 写出具体原因或拆步 |
| Proof 连续无空行 | 多步推导挤在一起 | 步骤之间加空行 |

---

## 15. 人工审阅清单

### A. 符号与 Notation
1. Transpose 是否统一用 `\top`?`T` 是否只表示 iteration?
2. 矩阵维度符号是否有语义关系?是否有无意义命名?
3. 向量是否统一用 `bmatrix`?
4. Norm 写法是否统一?norm 类型是否明确?
5. 概率 `\Pr` / 期望 macro 是否全文统一?
6. `[d]`、inner product、Hadamard product 是否有定义?
7. 从其他 paper 合并的 notation 是否已迁移?
8. 集合条件分隔符(`:` vs `\mid`)是否统一?

### B. Proof 逻辑
1. 每步是否只有一个原因?是否有跳步?
2. Reason 是否真实?是否有空洞的 "clearly"?
3. 所有 named inequality / theorem 是否有 citation?
4. Proof 是否 self-contained?符号是否全部有定义?
5. 防御性常数:δ 分配是否 top-down?是否留有余地?
6. Big-O 内是否有无意义常数?

### C. 结构与 Roadmap
1. Main body / appendix roadmap 是否存在且与实际一致?
2. Informal/formal 双版本是否互相引用?label 是否区分 `_informal`/`_formal`?
3. Appendix formal statement 是否条件完整(不写 "same as before")?
4. 正文中 "proof in Appendix X" 是否指向正确?

### D. Citation 与 BibTeX
1. 所有标准工具/定理首次出现是否有 citation?
2. BibTeX key 是否 lastname+year 格式?
3. 引用优先级:journal > conference > arXiv?
4. 是否有重复 bib 条目或断链?

### E. 源码与协作
1. Label 名是否有意义(非编号式)?
2. 分数排版:长分子短分母是否改 inline?
3. TeX 源码不看 PDF 能否理解结构?
4. Overleaf comments 是否全部处理?
5. 复制来的内容是否已改成当前 paper 风格?

---

## 16. 改稿后检查顺序

每次大改 paper 后,按此顺序检查:

1. **结构**:section 顺序、proof 在正文 vs appendix、informal/formal 双版本
2. **Label**:统一命名、所有 `\ref`/`\eqref` 正确、无重复/未定义 label
3. **Roadmap**:main body + appendix + section-level(如有)
4. **Citation**:所有工具/定理/数据集/baseline 的 citation,bib key 风格统一
5. **Proof 一致性**:main text 与 appendix 对齐、条件一致、notation 无漂移
6. **Linter**:`latex_lint.py` 扫描,修复 ERROR,复核 WARN
7. **Comments**:所有 TODO / Overleaf comment 全部处理或明确保留
