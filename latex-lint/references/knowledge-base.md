# 规范来源与详细说明

本文档记录每条规范的出处和完整上下文，供深入理解时参考。

## 来源

所有规范提炼自 B 站 UP 主 @simapofang（司马老师）的「打字抄能力」系列视频。
该系列记录了一个理论 CS/ML 课题组在 Overleaf 上协作写论文时积累的 LaTeX 实战经验。

## Label 命名详解

**来源**: 第 1 期「LaTeX 书写规范」

- 三字母前缀是为了让 label 在 TeX 源码中一眼可识别类型
- 下划线分隔是因为减号和空格在中英文混排环境下可能产生编码问题
- "你觉得你爸你妈把你叫张一张二张三吗？" — label 名应该是有意义的英文单词概括
- 同时写五篇文章时，有意义的 label 名才能区分上下文
- Label 是 ID（证件号码），display name 是名字 — 一个用于唯一引用，一个用于展示
- 两个相同 label 会报 warning，就像两个人不可能有相同的 SSN

**`[display name]` 和 `\label` 顺序**:
```latex
% 正确
\begin{lemma}[Cauchy-Schwarz]\label{lem:cauchy_schwarz}
% 错误 — 交换顺序可能产生 bug
\begin{lemma}\label{lem:cauchy_schwarz}[Cauchy-Schwarz]
```

## 引用格式详解

**来源**: 第 1 期、第 104 期

- `\ref` 不带括号，`\eqref` 自带括号
- Equation 引用统一用 `Eq.~\eqref{eq:xxx}` 格式
- Theorem/Lemma 引用用 `Lemma~\ref{lem:xxx}` 格式
- `~`（波浪线）产生不换行空格 — "这是一个习惯，这样会好一些"
- Equation label 前缀用 `eq:` 不要写 `equation:` — 简洁高效

## Equation 环境详解

**来源**: 第 1 期

- 未被引用的 equation 用 star 环境（不编号）
- 不要同时出现 `\label` 和 star — 会冲突报 warning
- 用 `\notag` 而非 `\nonumber` — 纯粹是统一规范
- "很多事情就是……我做了十几年科研，总结出来的一个高效打字的事情"

## 括号与分数详解

**来源**: 第 1 期

- "很多学生喜欢用 `\big \left` 把括号变得非常大——这一般来说没有意义"
- "你不需要任何一个括号 size，你打的时候就不要用变大变小，我做好了过一遍就可以了"
- 只有 advisor 在最终 pass 时统一调整括号大小
- 分数选择：上下一样长用 `\frac`，不平衡时考虑 inline 形式
- "我一般写 LaTeX 时候，我是不看 PDF，直接看 TeX"— 所以源码可读性很重要

## 定义符号详解

**来源**: 第 104 期、第 328 期

- "我们定义的时候用冒号等号，不要用等号双尖括号"
- "不管别人怎么用，你都用冒号等号" — 统一规范比跟随他人更重要
- "别人吃真巧克力，你不应该也跟着吃真巧克力" — 别人的不规范写法不能照搬

## Proof 写作详解

**来源**: 第 1 期、第 104 期、第 232 期

### 换行与可读性
- "你不要写一个特别长的证明，特别糊的证明。你尽量就是写证明就是多换行"
- Equation 后面要补原因时，应该换行再写——不要紧接在 equation 后面
- "这就跟问你 yes or no，你说了个 yes 之后，紧接着说了一句话，我就不记得那个 yes 是啥了"

### 每步一因
- 每一步推导应该只用一个原因
- "如果某一步需要两个原因，那就意味着这一步应该拆成两步"
- 示例：不要直接写 1 ≤ 5，应该写 1 ≤ 2（原因 A）≤ 3（原因 B）≤ 5（原因 C）

### 防御性写证明
- "做人要给别人台阶下，写常数要给修改留有余地"
- 概率 union bound 时，不要用精确的 δ/4（因为加一个 part 就要全部改成 δ/5）
- 应该用 δ/10 — 用十进制调参，未来调整最小化
- "你不知道意外和明天哪个先来"
- "固定参数（如 M）可以不留余地，但常数可能千变万化"
- log 中的 power 必须提取出来：任何文章在 log 里写 power 都是 "death reject, 没有接受过教育"
- 顶层设计：先定目标（如总失败概率 1-δ），top-down 推导每层需要的概率

## BibTeX 详解

**来源**: 第 1 期、第 82 期

### Key 命名
- 用 last name + 年份：`he2016`
- 1-4 个作者：写出所有 last name 首字母
- 5+ 个作者：用 `abc` + 年份
- "很多学生洗完之后会变成 first name，你要把它改成 last name"
- 同年同作者：加字母后缀 `a`, `b`, `c`

### 引用来源优先级
1. Journal 版本（最权威）
2. Conference 版本
3. arXiv 版本（预印本）
4. 始终引用最新 version

### 4 种 citation case
1. 有 Google Scholar → 直接点 BibTeX 复制
2. 只有 arXiv → 找一个 arXiv BibTeX 模板，替换字段
3. 中了 conference 但无 Scholar → 找对应 conference 的 BibTeX 模板
4. 只有 personal link → 搜索 "how to cite a webpage in BibTeX"

## Roadmap 详解

**来源**: 第 118 期

- Main body roadmap：放在 related work 后面或 intro 末尾
- Appendix roadmap：放在 appendix 开头
- Section roadmap：当 section 有很多 subsection 时可选
- 前两者是**必须**的
- 格式：`\paragraph{Roadmap.}` + 每个 section 的一句话概括
- **每次修改论文结构后，必须检查所有 roadmap 是否一致**

## Informal / Formal Label 详解

**来源**: 第 118 期

论文中同一个 theorem 可能在 main body（简化版/informal）和 appendix（完整版/formal）各出现一次：

| 场景 | Main TeX | Appendix |
|------|----------|----------|
| 两者都有 | `:informal` | `:formal` |
| 只在 main | `:informal` | 无后缀 |
| 只在 appendix | 无后缀 | `:formal` |

目的：方便互相引用，同时区分两个版本。

## Named Inequality 必须有 Citation

**来源**: 第 123 期

每个使用到的 named inequality / theorem 必须有 citation：
- Markov inequality
- Chebyshev inequality
- Hoeffding inequality / bound
- Jensen inequality
- Cauchy-Schwarz inequality
- 其他任何以人名命名的不等式

"以后这种 well-known inequality 不需要给证明，但需要给 citation。"

同时应该写一个 remark 记录这些 inequality 在论文的哪些位置被使用。

## Norm 选择讨论

**来源**: 第 86 期

- ε-net 可以用不同的 norm 定义（L∞, L2, L1）
- 不同 norm 的 net 上点数不同
- 选择 norm 涉及两个 trade-off：net size vs. Lipschitz constant 
- 建议在论文中写一个 discussion subsection 列出不同 norm 的结果对比
- "reviewer 一旦问了这个问题，咱们绝对绕不清楚" — 提前在文中说清楚
