---
# Anti-Vibe Checklist：避免 AI 生成论文痕迹

> 来源：资深 reviewer 在审稿中总结的真实 signal，能让 reviewer 一眼判断是否为"纯 vibe paper"并直接压分。
> 写作时用作反向 checklist——每条都是应当**避免**的。

---

## 1. Introduction

- [ ] **Motivation 引入是否有铺垫？** — intro 只有一两段、motivation 生硬跳出是最明显的 vibe 信号；应有足够的 background 铺垫自然引出问题
- [ ] **贡献点是否真实对齐方法？** — 避免 overclaim（用户让模型"做一个 X 的方法"，AI 会在全文反复强调 X 而不管 X 是否真的核心）

---

## 2. Method

- [ ] **所有符号在使用前是否有 denote？** — 符号/公式未定义就上、公式极度零碎（一两句话后就跟一串公式）是典型 AI 写作风格
- [ ] **算法伪代码是否必要？** — 堆砌没必要的 Algorithm block 是常见 vibe 填充手段；若伪代码只是重复了已有的文字描述，应删去
- [ ] **Theorem / 理论是否真正支撑方法？** — AI 生成的定理要么只是现有结论的改写、要么与上下文方法的关联极其松散；每个定理应在正文中明确说明其对 method 的意义
- [ ] **在 method 部分是否出现 baseline 比较？** — baseline 比较属于 experiment，提前出现是 motivation 混乱的信号
- [ ] **Motivation 是否发生漂移？** — AI 会把 high-level motivation 突然转移到某个细枝末节（用户让它改一小块，它就在正文里大书特书这个局部需求）；每节的 motivation 应始终对齐全局主线

---

## 3. 行文组织

- [ ] **Bullet 使用是否合理？** — 滥用 bullet 组织本应是段落叙述的内容；尤其注意 bullet 之间是递进/因果关系时，不应写成平行列表
- [ ] **模块命名是否简洁一致？** — 模块名冗长、全文缩写前后不一致是明显信号；避免对模块名滥用加粗强调

---

## 4. 语言风格

- [ ] **是否有 AI 特征句式？**
  - 分号（`;`）和破折号（`—`）滥用
  - `therefore` / `thus` 放句子中间而非句首
  - 套路化的段落开头（*In this section, we present...*）
- [ ] **是否堆砌华而不实的副词/形容词？** — 如 *elegantly*、*theoretically*、*seamlessly*、*effectively*；这类词在学术写作中几乎没有信息量，应删除或替换为具体描述
- [ ] **Related works 的引用与文本是否真正匹配？** — AI 生成的 related works 常出现文字描述和 `\cite` 完全对不上的情况；每条引用前应人工核查

---

## 5. Experiment

- [ ] **分析是否回扣 main motivation？** — ablation / analysis 部分只报数字、不解释数字如何印证或深化 intro 里的 motivation，是区分优秀论文与 vibe 论文的关键
- [ ] **是否仍在滥用 bullet 和加粗？** — 实验部分的 bullet 和粗体应只用于真正需要强调的结论，而非用来填充篇幅
- [ ] **（Empirical / non-method 论文）故事线是否完整？** — AI 难以把一系列小实验串成连贯叙事；findings 应显式提炼，而非只罗列结果

---

## 6. 配图

- [ ] **AI 生成图是否经过人工修改？** — 直接使用 Banana / 类似工具输出的流程图、pipeline 图，风格单一且一眼可辨；应结合项目实际修改样式、颜色、排布
- [ ] **数据驱动图表是否用代码绘制？** — bar chart / line plot / heatmap 应用 matplotlib/seaborn 绘制，不要用 AI 图像生成

---

## 7. Appendix

- [ ] **Appendix 是否有人工把关？** — Appendix 是 AI 痕迹最集中的区域（很多作者赌 reviewer 不看）；reviewer 一旦翻开印象分会大幅下降
- [ ] **Appendix 内容是否与正文真正互补？** — 不应只是正文的重复展开，应包含完整推导、额外实验、实现细节等真正有价值的内容

---

## 快速自查（写完后过一遍）

| 区域 | 核心问题 |
|------|---------|
| Intro | motivation 铺垫够吗？贡献没有 overclaim？ |
| Method | 公式有 denote？伪代码必要？定理有实质作用？没有提前比 baseline？ |
| 行文 | bullet 是真正的列表而非伪段落？模块名简洁一致？ |
| 语言 | 没有分号/破折号滥用？没有华而不实副词？related works 引用核查过？ |
| Experiment | 分析回扣了 motivation？ |
| 配图 | AI 图经过人工修改？ |
| Appendix | 人工检查过，有实质内容？ |
