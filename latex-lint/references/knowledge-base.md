# 规范来源与详细知识库

本文档记录每条规范的完整出处与上下文。整理自 B 站 @simapofang「打字抄能力」系列。
该系列记录了一个理论 CS/ML 课题组在 Overleaf 上协作写论文的实战经验。

> "打字抄能力里的 LaTeX 不是'把代码敲对'，而是'把一篇 paper 写成长期可维护、可协作、可检查、可扩展的技术文档'。"

---

## 一、总原则

### 1.1 三层目标（第1期、第117期）

- **短期**：能正确编译，PDF 不难看
- **中期**：coauthor 能读懂源码，能快速定位和修改
- **长期**：写第十篇、第二十篇 paper 时，写作系统仍然稳定、统一、可复用

### 1.2 统一风格比"我觉得也行"更重要

多人协作时，统一风格本身就是价值。对初学者，最现实的选择是先照着成熟规范写。

### 1.3 复制粘贴的风险（第117期）

复制代码最大风险不是不能编译，而是：
- 不知道 environment 干什么
- 不知道符号为什么这样定义
- 别人的 notation system 被机械搬入，与当前 paper 打架

> "别人吃真巧克力，你不应该也跟着吃。抄过来的东西要按我们的规范改成我们的 style。"

### 1.4 "能自己吃饭"的标准（第117期）

> 给你一篇 paper，你从头写一版；别人检查时几乎一个字都不用改。

在那之前，不要随便改 bracket size、发明 notation、照搬别人写法。

### 1.5 Author responsibility（第291期）

> "这不是我写的"不能成为不检查的理由。只要你是作者，就有责任检查每个符号、每个 statement、每个 proof。

---

## 二、Label 详解（第1期）

### 2.1 "证件号"类比

- Label 是 SSN（唯一 ID），display name 是名字
- 两个相同 label 报 warning，就像两个人 SSN 不能一样

### 2.2 命名

- 三字母前缀 + 冒号 + 下划线分隔的有意义英文单词
- "你爸你妈把你叫张一张二张三吗？"——label 要有语义
- 同时写五篇文章时，有意义的 label 才能区分上下文

### 2.3 `[display name]` 与 `\label` 顺序

```latex
% 正确
\begin{lemma}[Cauchy--Schwarz]\label{lem:cauchy_schwarz}
% 错误——交换可能产生 bug
\begin{lemma}\label{lem:cauchy_schwarz}[Cauchy--Schwarz]
```

### 2.4 Informal / Formal（第118期）

| 场景 | Main TeX | Appendix |
|------|----------|----------|
| 两者都有 | `_informal` | `_formal` |
| 只在 main | `_informal` | 无后缀 |
| 只在 appendix | 无后缀 | `_formal` |

---

## 三、引用格式详解（第1期、第104期）

- `\ref` 不带括号，`\eqref` 自带括号
- Equation：`Eq.~\eqref{eq:xxx}`（不写全称 Equation，用 `~` 不换行空格）
- Theorem/Lemma：`Lemma~\ref{lem:xxx}`
- Equation label 前缀 `eq:` 不要写 `equation:`

---

## 四、Equation 环境（第1期）

- 未引用的 equation 用 star 环境不编号
- Star 环境 + `\label` 会冲突报 warning
- 统一用 `\notag`（不用 `\nonumber`）

---

## 五、括号与分数（第1期、第117期）

### 5.1 Bracket sizing

> "很多学生喜欢用 `\big \left` 把括号变很大——一般没意义。你不需要任何括号 size 调整，我做好了过一遍就行。"

初学者规则：**不动 bracket size，保持默认**。

### 5.2 分数

- Display equation 中复杂分式用 `\frac`
- Inline 中简单分数用 `1/2`（比 `\frac{1}{2}` 更紧凑）
- 不对称分子分母（长分子短分母）考虑改写

---

## 六、数学符号详解

### 6.1 定义符号 `:=`（第104期、第328期）

> "定义的时候用冒号等号，不管别人怎么用，我们都用冒号等号。"

### 6.2 Transpose `\top`（第117期）

`T` 常表示 iteration horizon（`x_1, ..., x_T`），与 transpose 冲突：

```latex
x^\top A x    % 推荐
x^T A x       % 不推荐——T 可能是 iteration
```

### 6.3 容错性 Notation（第117期）

Pseudo-inverse 用 `\dagger` 而非 `^+`——因为如果 `^+` 打错，可能变成普通加法 `A + B`，难以发现。

> 初学者项目中的 notation 要考虑"写错后能不能被唯一修回来"。

### 6.4 概率与期望（第104期）

- 用项目已有 macro：`\E`、`\Pr`
- 不要一会儿 `\mathbb{E}`，一会儿 `E`，一会儿自定义 `\expectation`
- 下标位置要正确：`\E_{X \sim P}[f(X)]`

### 6.5 Norm 写法（第86期、第123期、第162期标题）

```latex
\|x\|_1, \|x\|_2, \|x\|_\infty, \|A\|_F
```

- 用 `\|` 不用键盘 `||`
- 不要滥用 `\left\|`/`\right\|`
- 选择 norm 要和证明需求一致（不同 norm 的 net size、Lipschitz 常数不同）

### 6.6 对数中的幂次

> "任何文章在 log 里写 power 都是 death reject，没有接受过教育。"

`\log(a^d)` → `d \log(a)`，所有 power 移到外面。

### 6.7 Notation 系统设计（第117期）

好的 notation 应满足：
1. 语义清楚
2. 全文一致
3. 避免冲突
4. 容易排错
5. 可扩展
6. 符合领域习惯

矩阵维度要有语义关系：

```latex
X \in \mathbb{R}^{n \times d}, W \in \mathbb{R}^{d \times k}  % 好
A \in \mathbb{R}^{u \times c}, B \in \mathbb{R}^{a \times q}  % 坏——无语义
```

---

## 七、向量与矩阵（第148期）

向量用方括号矩阵：

```latex
x = \begin{bmatrix} x_1 \\ x_2 \\ \vdots \\ x_d \end{bmatrix}
```

不用 `pmatrix`（圆括号）。方括号更常见、减少歧义。

基础 notation：
- `[d] := \{1, ..., d\}`
- Inner product: `\langle a, b \rangle = a^\top b`
- Hadamard product: `x \odot y`

---

## 八、Proof 写作（第1期、第104期、第232期、第439期、第440期）

### 8.1 多换行

> "不要写特别长特别糊的证明。多换行。"

Equation 后换行再写原因，不要紧接同一行。

### 8.2 一步一因

每步推导只用一个原因。三个原因就拆成三步：

```latex
A &\le B && \text{by Lemma~\ref{lem:first}} \\
  &\le C && \text{by Jensen's inequality} \\
  &\le D && \text{by a union bound}
```

### 8.3 Reason 必须真实

> 第440期以"抽象指数 abstract value"开玩笑——proof step 的 reason 必须真的解释这一步。

不能写 `clearly`（当这步对读者并不 clear 时）。

### 8.4 不确定时留 TODO

```latex
% TODO(name): I think this uses Markov's inequality but not sure how to set the RV.
```

### 8.5 Self-contained proof（第104期）

Proof 依赖的工具要明确写出 statement + citation + reference：
- Markov, Chebyshev, Hoeffding, Bernstein, Jensen, Cauchy-Schwarz
- Composition theorem, net covering number lemma 等

### 8.6 防御性写证明（第232期）

**核心思想：给未来修改留余地。**

- 概率 union bound 用 δ/10 不用 δ/4——加一个 event 不用全改
- 常数用十进制：0.1 而非 0.25, 0.223
- Top-down 设计：先定目标 1-δ，再分配每层
- 固定参数（如 M）可以不留余地，但常数可能千变万化
- 常数要么精确算，要么用 O(·) 隐藏——不要 `O(16d log n)`

> "做人要给别人台阶下，写常数要给修改留有余地。你不知道意外和明天哪个先来。"

### 8.7 Clean statement（第439期）

- 常数能写清楚就写：`2\sqrt{a+b}` 而非 `C\sqrt{a+b}`
- 条件不要多余：如果可以算出 `x ≥ e^4` 就不要写 "sufficiently large"
- 可以 provide proof 也可以不 provide，但要知道为什么

---

## 九、BibTeX（第1期、第82期）

### 9.1 Key 命名

- Last name + 年份：`he2016`
- 1-4 作者写出 last name
- 5+ 作者用首字母 + 年份：`abc2024`
- 同年同作者加后缀：`he2016a`, `he2016b`
- "很多学生会写成 first name，要改成 last name"

### 9.2 4 种 citation case（第82期）

1. 有 Google Scholar → 直接复制 BibTeX，改 key
2. 只有 arXiv → 找 arXiv BibTeX 模板替换字段
3. 中了 conference 无 Scholar → 找对应 conference BibTeX 模板
4. 只有 personal link → 搜索 "how to cite webpage in BibTeX"

### 9.3 引用优先级

Journal > Conference > arXiv，始终引用最新 version。

### 9.4 每个 named inequality 要 citation（第123期）

> "这个 Markov inequality 要给 citation。Chebyshev 也要。Hoeffding 也要。所有这些都需要给 citation。"

写 remark 记录在文章哪些位置使用。

---

## 十、Roadmap（第118期）

### 10.1 位置

- Main body roadmap：intro 末尾或 related work 后（**必须**）
- Appendix roadmap：appendix 开头（**必须**）
- Section roadmap：subsection 多时可选

### 10.2 格式

```latex
\paragraph{Roadmap.}
The remainder is organized as follows.
In Section~\ref{sec:prelim}, we introduce ...
```

### 10.3 维护

> 每次修改论文结构后，必须检查所有 roadmap 是否一致。

---

## 十一、Definition / Theorem / Lemma / Fact / Claim（第328期标题、第291期）

- **Definition**：引入概念，不需 proof，定义用 `:=`
- **Fact**：标准事实，label 用 `fac:`，需 citation
- **Lemma**：中间结论，需 proof
- **Theorem**：主要结论
- **Claim**：局部小结论，可在 proof 内部使用

Appendix formal statement 要写得 sparse（条件列全）：

```latex
\begin{lemma}[Formal version of Lemma~\ref{lem:xxx_informal}]
\label{lem:xxx_formal}
Suppose:
\begin{enumerate}
    \item $n \ge ...$;
    \item $\delta \in (0,1)$;
    \item Assumption~\ref{ass:lipschitz} holds.
\end{enumerate}
Then ...
\end{lemma}
```

不要写 "Under the same assumptions as before"——appendix 离 "before" 太远。

---

## 十二、协作习惯（第1期、第120期、第291期）

### 12.1 Overleaf comments

- 创建 name tag，在具体位置留 comment
- 完成后在 thread 中说明 finished/done
- Comment 要有质量：指向具体位置、说明具体问题

### 12.2 `%` 注释

像 Git commit message 一样，源码注释帮助未来维护：
- 临时占位
- 不确定的 proof step
- Notation 为什么这样定义
- 某个 trick 参考了哪篇 paper

### 12.3 源码可读性

> "我一般写 LaTeX 的时候，不看 PDF，直接看 TeX。"

---

## 十三、Merge notation system（第117期、第162期标题）

合并两篇 paper 的 notation 时：

1. **列表**：列出两套系统的对照表
2. **确定主系统**：选和本文最相关、最少冲突的
3. **逐个迁移**：不只是 find-and-replace，要检查维度、下标、含义
4. **写 notation table**：在 preliminaries 中说清楚

---

## 十四、Norm 选择讨论（第86期）

ε-net 可用不同 norm 定义——不同选择影响 net size、Lipschitz 常数、最终 bound。

> "reviewer 一旦问了这个问题，绝对绕不清楚——提前在文中写 discussion subsection 说清楚。"

---

## 十五、算法环境（第165期标题，字幕缺失）

保守建议：

```latex
\begin{algorithm}[t]
\caption{Training procedure}\label{alg:training}
\begin{algorithmic}[1]
\Require Dataset $D$, step size $\eta$
\Ensure Model parameter $\theta$
\State Initialize $\theta_0$
\For{$t=1$ to $T$}
    \State $g_t \gets \nabla f(\theta_{t-1})$
    \State $\theta_t \gets \theta_{t-1} - \eta g_t$
\EndFor
\State \Return $\theta_T$
\end{algorithmic}
\end{algorithm}
```

函数名用 small caps：`\textsc{Encode}`, `\textsc{Decode}`, `\textsc{Sample}`

---

## 十六、图片插入（第181期）

已知问题：多图排版直接 `\includegraphics` 容易产生大量空白。
该期未给出最终解法。基本起点：

```latex
\begin{figure}[t]
    \centering
    \begin{subfigure}{0.19\linewidth}
        \includegraphics[width=\linewidth]{figures/a.pdf}
        \caption{}
    \end{subfigure}\hfill
    \begin{subfigure}{0.19\linewidth}
        \includegraphics[width=\linewidth]{figures/b.pdf}
        \caption{}
    \end{subfigure}
    \caption{...}\label{fig:multi}
\end{figure}
```

---

## 十七、Slides 日期格式（第148期）

```
August 8, 2024
```

月份首字母大写 + 空格 + 日期 + 英文逗号 + 空格 + 年份。
