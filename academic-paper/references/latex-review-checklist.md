---
# LaTeX Review Checklist（人工复查用）

写完后 review agent 逐项检查并向用户汇报。先跑 linter，再走此清单。

```bash
# 先跑 linter（自动捕获硬规则）
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py <file> --bib --severity WARN
```

---

## A. 符号与 Notation

- [ ] Transpose 全文统一用 `\top`？`T` 是否只表示 iteration horizon？
- [ ] Norm 写法统一（`\|x\|`）？norm 类型明确（ℓ₁ / ℓ₂ / Frobenius / …）？
- [ ] 所有定义用 `:=`？无 `\triangleq` 或裸 `=` 定义？
- [ ] 矩阵维度符号有语义（`n×d`），而非无意义字母（`u×c`）？
- [ ] 向量统一用 `bmatrix`（方括号），未用 `pmatrix`？
- [ ] `[d] := {1,...,d}` 在 preliminaries 中有定义（如使用）？
- [ ] `\E` / `\Pr` macro 全文一致？
- [ ] 集合条件分隔符（`:` vs `\mid`）全文统一？
- [ ] 从其他 paper 引入的 notation 已迁移为当前 paper 风格？

## B. 证明逻辑

- [ ] 每步只有一个 reason？无从 A 跳到 E 的跨步？
- [ ] 无 `clearly` / `obviously` 掩盖未解释的步骤？
- [ ] 每个 named inequality 有 citation（Markov、Hoeffding、Jensen、Bernstein、Cauchy–Schwarz …）？
- [ ] Proof self-contained：所有用到的符号均有定义或引用？
- [ ] 失败概率 δ 采用 top-down 分配（δ/10 而非 δ/4，留余地）？
- [ ] 常数：要么精确写出，要么藏进 O(·)——不要两种混用？
- [ ] Appendix formal statement 条件完整列出（不写 "same assumptions as before"）？

## C. 结构与 Roadmap

- [ ] Main body 有 `\paragraph{Roadmap.}`（intro 末或 related work 后）？
- [ ] Appendix 开头有 roadmap？
- [ ] Roadmap 中引用的 section / theorem 编号与实际一致？
- [ ] Informal/formal 双版本：main 用 `_informal`，appendix 用 `_formal`？
- [ ] 正文中 "proof in Appendix X" 指向正确？

## D. Label 与交叉引用

- [ ] 所有 label 使用正确前缀（`eq:` `lem:` `thm:` `fig:` `tab:` …）？
- [ ] Label 名有语义，非 `eq:1` / `lem:a`？
- [ ] 所有被 `\ref`/`\eqref` 引用的元素都有 `\label`？
- [ ] 每个 figure / table / algorithm 在正文中有 `\ref`？
- [ ] 无 undefined label / multiply-defined label 编译警告？

## E. Citation 与 BibTeX

- [ ] 所有引用用 `\citet`/`\citep`，无手写 `[1]` 或 `(Author, Year)`？
- [ ] BibTeX key 符合 `lastname+year` 格式？
- [ ] 引用优先级：journal > conference > arXiv？
- [ ] 自引比例合理（< ~20%）？
- [ ] 无重复 bib 条目或断链？
- [ ] 所有标准工具/定理首次使用处有 citation？

## F. 排版细节

- [ ] 表格用 `booktabs`，caption 在上方，最优结果加粗？
- [ ] 图片 caption 在下方，self-contained，字号不小于正文 80%？
- [ ] 灰度打印时图表仍可区分不同曲线/区域？
- [ ] 数字精度在同列/同上下文内统一？
- [ ] 缩写首次出现时展开？

## G. 源码质量

- [ ] TeX 源码不看 PDF 即可理解结构（合理空白、缩进）？
- [ ] 关键选择有 `%` 注释（为何这样定义符号、参考了哪篇 paper）？
- [ ] 所有 Overleaf comments 已处理或明确标记为保留？
- [ ] 复制来的内容已改成当前 paper 的 notation / style？

---

## 汇报格式

```markdown
## LaTeX Review 结果

**文件**: <path>  **日期**: <date>

### ❌ 必须修复
1. [B] 第 3 步 `clearly` 掩盖了 Jensen 不等式的使用——请显式写出
2. [D] `\label{eq:1}` 语义不明，建议改为 `eq:kl_divergence`

### ⚠️ 建议改进
1. [A] `T` 在第 4 节同时表示 transpose 和 iteration horizon，存在歧义

### ✅ 已通过
- A: 符号与 Notation — notation 系统一致
- E: Citation & BibTeX — 格式规范，优先级正确
```
