---
name: latex-lint
description: 基于「打字抄能力」系列的 LaTeX 学术写作规范检查。当用户请求检查 LaTeX 源码规范、论文排版质量、proof 写作风格时触发。内置 linter 脚本自动检测常见问题（label 命名、引用格式、bracket sizing、BibTeX key、norm 写法、transpose、常数美学等），并提供修复建议。适用于："帮我检查 LaTeX""论文格式检查""lint my tex""proof 写法有没有问题""检查一下 overleaf 项目""notation 有没有问题"。
---

# LaTeX Lint — 学术 LaTeX 写作规范检查

基于 B 站 @simapofang「打字抄能力」系列提炼的 LaTeX 学术写作规范。
核心理念：**LaTeX 不是"能编译就行"，而是"能长期维护、可协作、可检查、可扩展"的技术文档。**

详细知识库与出处见 `references/knowledge-base.md`。

## 快速开始

收到用户的 LaTeX 检查请求后：

1. 确定要检查的 `.tex` / `.bib` 文件路径
2. 运行 linter 脚本：
   ```bash
   python3 <skill-dir>/scripts/latex_lint.py <file-or-directory> [--bib] [--fix-preview]
   ```
3. 阅读 linter 输出，按严重程度排序向用户汇报
4. 对 linter 无法覆盖的语义问题，阅读下方人工审阅清单逐项检查
5. 给出具体修复建议和示例代码

## 规范总览

以下规范按类别组织。每条标注 `[AUTO]`（脚本可检测）或 `[MANUAL]`（需人工审阅）。

---

### 1. Label 命名

- `[AUTO]` Label 使用三字母前缀 + 冒号：`thm:`, `lem:`, `cor:`, `def:`, `fac:`, `sec:`, `eq:`, `fig:`, `tab:`, `alg:`, `app:`, `rem:`, `prop:`, `ass:`, `cla:`
- `[AUTO]` Label 名全小写，用下划线分隔单词：`lem:cauchy_schwarz` ✓，`Lem:Cauchy-Schwarz` ✗
- `[AUTO]` 不用减号或空格
- `[MANUAL]` Label 名应有意义——用一两个英文单词概括内容，不要用 `eq:1`, `lem:a` 式编号。"不要叫张一张二张三"——这不影响第一篇文章，但影响第十篇
- `[AUTO]` 对于 main tex + appendix 双版本，main 用 `_informal` 后缀，appendix 用 `_formal` 后缀
- `[AUTO]` `\label` 必须在 `[display name]` 之后——交换顺序会产生 bug
- `[AUTO]` Equation label 前缀用 `eq:` 不要写全称 `equation:`

### 2. 引用格式

- `[AUTO]` Equation 引用：`Eq.~\eqref{eq:xxx}` — 不写完整 `Equation`，不用 `\ref`
- `[AUTO]` Theorem/Lemma/Definition/Section/Figure/Table 引用：`Lemma~\ref{lem:xxx}` — 波浪线 `~` 产生不换行空格
- `[AUTO]` `\ref` 不带括号，`\eqref` 自带括号 — 不要在 equation 上用 `\ref`，不要在非 equation 上用 `\eqref`
- `[AUTO]` 引用前必须有 `~`（non-breaking space）

### 3. Equation 环境

- `[AUTO]` 未被引用的 equation 使用 star 环境或 `\notag`
- `[AUTO]` 不要在 star 环境中放 `\label` — 冲突报 warning
- `[AUTO]` 使用 `\notag` 而非 `\nonumber`（统一规范）
- `[AUTO]` Equation label 前缀用 `eq:`

### 4. 括号与分数

- `[AUTO]` 不要自行使用 `\big`, `\Big`, `\bigg`, `\Bigg` — 保持默认大小，留给 advisor 统一调整
- `[AUTO]` 不要过度使用 `\left`/`\right` — 初学者不应动 bracket size
- `[MANUAL]` 分数：display equation 中复杂分式用 `\frac`；inline 中简单分数用 `1/2`；不对称分子分母考虑改写避免排版失衡

### 5. 数学符号与定义

- `[AUTO]` 定义新符号用 `:=`，不用 `=` 或 `\triangleq`。"别人吃真巧克力，你不应该跟着吃"
- `[AUTO]` 概率用 `\Pr`，期望用 `\E` / `\mathbb{E}` — 用项目已有 macro，不要自己发明
- `[AUTO]` Transpose 用 `\top`（`x^\top`），不用 `^T` — 因为 `T` 常表示 iteration horizon，冲突
- `[AUTO]` Norm 用 `\|x\|`，不用键盘 `||x||`
- `[AUTO]` 对数中幂次提取出来：`\log(a^d)` → `d \log(a)`。"在 log 里写 power 是 death reject"
- `[AUTO]` big-O 内不要放无意义常数：`O(16d\log n)` → `O(d\log n)`
- `[MANUAL]` 向量用 `\begin{bmatrix}...\end{bmatrix}`（方括号），不用 `pmatrix`（圆括号）
- `[MANUAL]` 每个 named inequality / theorem 必须有 citation（Markov, Chebyshev, Hoeffding, Jensen, Bernstein 等）
- `[MANUAL]` Notation 不是随机字母游戏——符号要有语义、全文一致、避免冲突、可扩展

### 6. Proof 写作风格

- `[AUTO]` Proof 中步骤之间应有空行分隔——不要写成一坨
- `[AUTO]` 检测 `clearly` / `obviously` 等可能掩盖不清楚步骤的词
- `[MANUAL]` 每一步推导只写一个原因；需要多个原因就拆成多步
- `[MANUAL]` 展示中间步骤——不要从 A 直接跳到 E
- `[MANUAL]` Proof 应 self-contained：所有用到的符号都要有定义或引用
- `[MANUAL]` 每个 proof step 的 reason 必须真实——不能写 "by abstract value"
- `[MANUAL]` 不确定 reason 时留 TODO comment，不要写假 reason
- `[MANUAL]` 防御性写证明：概率常数用整数分母（δ/10 而非 δ/4），给未来修改留余地
- `[MANUAL]` 常数要么算清楚，要么用 O(·) 隐藏干净——不要两者同时出现
- `[MANUAL]` Failure probability 分配 top-down 设计：先定目标 1-δ，再分配到每层

### 7. BibTeX

- `[AUTO]` BibTeX key 格式：`lastname + year`（如 `he2016`）
- `[AUTO]` 5+ 作者用首字母：`abc2024`
- `[AUTO]` 同年同作者多篇用字母后缀：`he2016a`, `he2016b`
- `[AUTO]` Key 不要用 first name
- `[MANUAL]` 引用优先级：journal > conference > arXiv
- `[MANUAL]` 始终引用最新版本
- `[MANUAL]` 合并 bib 文件时：去重 DOI/title、统一 key 风格、检查断链

### 8. Roadmap

- `[AUTO]` Main body 在 intro 或 related work 后应有 `\paragraph{Roadmap.}`
- `[AUTO]` Appendix 开头应有 roadmap
- `[MANUAL]` Roadmap 引用的 section/theorem 编号必须与实际一致
- `[MANUAL]` 每次修改论文结构后检查所有 roadmap
- `[MANUAL]` Section-level roadmap：当 section 有很多 subsection 时可选

### 9. 源码可读性与协作

- `[AUTO]` 证明步骤之间应有空行
- `[MANUAL]` TeX 源码本身应可读——"我一般写 LaTeX 的时候，不看 PDF，直接看 TeX"
- `[MANUAL]` 必要的 `%` 注释：临时占位、不确定的 proof step、为什么这样定义 notation
- `[MANUAL]` Overleaf comments：指向具体位置、说明具体问题、完成后 resolve
- `[MANUAL]` 不要修改 advisor 已调整过的 bracket sizing
- `[MANUAL]` 复制别人论文内容后，必须按当前 paper 的 notation/style 改写

### 10. Notation 系统设计

- `[MANUAL]` 符号选择原则：语义清楚、全文一致、避免冲突、容错（写错后能从上下文修回）、可扩展、符合领域习惯
- `[MANUAL]` 矩阵维度符号应有语义关系：`X ∈ R^{n×d}` 而非 `A ∈ R^{u×c}`
- `[MANUAL]` 合并多篇论文 notation 时：列出两套系统、确定主系统、逐个迁移 proof、写 notation table
- `[MANUAL]` `[d] := {1,...,d}` 如使用需在 preliminaries 中定义
- `[MANUAL]` Inner product 用 `\langle a,b \rangle`，Hadamard product 用 `\odot`
- `[MANUAL]` 集合条件分隔符全文统一（`:` 或 `\mid`）

### 11. Definition / Theorem / Lemma / Fact / Claim 职责

- `[MANUAL]` Definition：引入概念，不需 proof，定义符号用 `:=`
- `[MANUAL]` Lemma：为证明 theorem 服务的中间结论，需 proof 或 citation
- `[MANUAL]` Theorem：主要结论
- `[MANUAL]` Fact：标准事实，label 用 `fac:`，需 citation
- `[MANUAL]` Claim：比 lemma 更局部，可能只在某个 proof 内部使用
- `[MANUAL]` Appendix formal statement 要条件完整、结构稀疏——用 "If the following conditions hold, then ..." 不要用 "Under the same assumptions as before"

### 12. 作者责任

- `[MANUAL]` "这不是我写的"不能成为不检查的理由——只要你是作者就有责任
- `[MANUAL]` Coauthor 的写法如果与规范冲突，要及时说明
- `[MANUAL]` 每个符号、每个 statement、每个 proof、每个 notation 都要检查

---

## Linter 脚本用法

```bash
# 检查单个文件
python3 <skill-dir>/scripts/latex_lint.py paper.tex

# 检查整个目录（自动递归 .tex）
python3 <skill-dir>/scripts/latex_lint.py ./my-paper/

# 同时检查 .bib 文件
python3 <skill-dir>/scripts/latex_lint.py ./my-paper/ --bib

# 预览修复建议
python3 <skill-dir>/scripts/latex_lint.py paper.tex --fix-preview

# 输出 JSON 格式
python3 <skill-dir>/scripts/latex_lint.py paper.tex --json

# 只显示 ERROR 和 WARN
python3 <skill-dir>/scripts/latex_lint.py paper.tex --severity WARN
```

严重级别：
- `ERROR`: 明确违反规范，应当修复
- `WARN`: 可能违反规范，建议检查
- `INFO`: 风格建议，非强制

## 人工审阅清单

Linter 之后，逐项人工检查：

### A. 符号与 Notation
1. Transpose 是否统一用 `\top`？`T` 是否只表示 iteration？
2. 矩阵维度符号是否有语义关系？是否有随机命名？
3. 向量是否统一用 `bmatrix`？
4. Norm 写法是否统一？metric/norm 类型是否明确？
5. 概率 `\Pr` / 期望 `\E` macro 是否统一？
6. `[d]` / inner product / Hadamard product 是否定义？
7. 从其他 paper 合并的 notation 是否已迁移？
8. 集合条件分隔符（`:` vs `\mid`）是否统一？

### B. Proof 逻辑
1. 每步是否只有一个原因？是否有跳步？
2. Reason 是否真实？是否有空洞的 "clearly"？
3. 所有 named inequality 是否有 citation？
4. Proof 是否 self-contained？符号是否全部有定义？
5. 防御性常数：δ 分配是否 top-down？是否留有余地？
6. 常数是否 clean？big-O 内是否有无意义常数？

### C. 结构与 Roadmap
1. Main body / appendix roadmap 是否存在且正确？
2. Informal/formal 双版本是否互相引用？label 是否区分？
3. Appendix formal statement 是否条件完整？
4. 正文中 "proof in Appendix X" 是否指向正确？

### D. Citation 与 BibTeX
1. 所有标准工具/定理首次出现处是否有 citation？
2. BibTeX key 是否 lastname+year？
3. 引用优先级：journal > conference > arXiv？
4. 是否有重复 bib 条目或断链？

### E. 源码与协作
1. Label 名是否有意义？
2. 分数排版：长分子短分母是否应改 inline？
3. TeX 源码不看 PDF 能否理解？
4. Overleaf comments 是否全部处理？
5. 复制来的内容是否已改成当前 paper 风格？

## 输出格式

```
## 🔍 LaTeX Lint 检查结果

### 自动检测（N 个问题）

| 级别 | 文件:行 | 规则 | 问题描述 | 修复建议 |
|------|---------|------|----------|----------|
| ERROR | ... | ... | ... | ... |

### 人工审阅发现（M 个建议）

1. **[类别]** 具体问题描述 + 修复建议 + 代码示例
```

## 改稿后检查顺序

每次大改 paper 后，按此顺序检查：

1. **结构**：section 顺序、proof 在正文 vs appendix、informal/formal 双版本
2. **Label**：统一命名、所有 `\ref`/`\eqref` 正确、无重复/未定义 label
3. **Roadmap**：main body + appendix + section-level
4. **Citation**：所有工具/定理/数据集/baseline 的 citation，bib key 风格
5. **Proof 一致性**：main text 与 appendix 对齐、条件一致、notation 无漂移
6. **Comments**：全部处理或明确保留

## 适用范围与限制

- 适用于学术论文（特别是理论方向 CS/ML 论文）
- 规范来自特定课题组的长期实践，不代表所有学术社区的共识
- 部分规范（如 bmatrix vs pmatrix）取决于领域传统
- Linter 基于正则匹配，可能产生 false positive——始终结合上下文判断
- 当前缺少字幕的专题（算法环境 `\textsc`、集合详细写法、bib merge 细则）待后续补充
