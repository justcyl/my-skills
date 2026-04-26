# 会议差异（Conference-Specific Analysis）

## 核心视角

不同会议有不同的 reviewer 文化和评审偏好。
读别人的论文时，了解它投的是哪个会议，有助于理解它的写作风格为什么是这样的。
写自己的论文时，针对目标会议做专项优化，是提高接受率的实际手段。

---

## 快速识别投稿目标会议

论文通常在以下地方标注：
- arXiv 页面的 "Comments" 字段（如 "Accepted at ICLR 2024"）
- 论文 PDF 页脚（如 "Under review as a conference paper at ICLR 2025"）
- 论文标题下方或首页注释

---

## 主要会议的文化与偏好

### ICLR（International Conference on Learning Representations）

**核心关键词**：理论严谨、新奇 insight、可复现、OpenReview 文化

**Reviewer 偏好：**
- 重视 **理论分析**（convergence proof、complexity bound、PAC 理论等）
- 重视 **新的 insight**，而不只是性能刷榜
- 对 **ablation study** 要求严格，要求每个设计选择都有实验支撑
- 非常重视 **reproducibility**：代码、超参数、随机种子

**ICLR 特有机制：**
- **OpenReview 公开审稿**：所有 reviewer 评论、author rebuttal、评分全部公开可查
- **评分机制**：通常 1-10 分（1=strong reject, 10=strong accept），3 分及以上才有机会
- **AC（Area Chair）决策权**：低分但有 oral/spotlight 提名的情况存在
- **Rebuttal 文化成熟**：作者可以逐条回复 reviewer，质量高的 rebuttal 真的会改变评分

**投稿 checklist：**
- [ ] 有没有 theoretical analysis 或 theoretical motivation？
- [ ] Limitation 节是否诚实、具体？
- [ ] 代码是否可以开源（或匿名提交）？
- [ ] 实验 setting 是否可以复现（hyperparameter、seed 都写了）？

---

### NeurIPS（Neural Information Processing Systems）

**核心关键词**：广度、影响力、社会影响

**Reviewer 偏好：**
- 范围最广，接受理论/应用/系统/数据集各类论文
- 重视 **Broader Impact**（论文的社会影响、潜在风险）
- 重视 **实验的充分性**（多数据集、多 baseline、统计显著性）
- 偏好有 **新颖视角** 的工作，即使是负面结果也可以接受

**NeurIPS 特有要求：**
- **Broader Impact 节**：需要明确讨论论文对社会的正面/负面影响
- **Checklist**：submission 阶段有 checklist，涵盖代码、数据、伦理等方面

**投稿 checklist：**
- [ ] Broader impact 节是否写了，内容是否有实质（不能只写"无负面影响"）？
- [ ] 实验是否有 error bar / significance test？
- [ ] 数据集是否公开/有 license？

---

### ICML（International Conference on Machine Learning）

**核心关键词**：理论深度、数学严谨

**Reviewer 偏好：**
- 比 NeurIPS 更偏理论，对 proof 要求更高
- 应用论文需要有扎实的理论 motivation 才容易接受
- 对 **novelty** 的定义严格：工程改进不够，需要有方法层面的创新

**投稿 checklist：**
- [ ] 核心方法是否有理论支撑（哪怕是直觉性的 theorem）？
- [ ] Contribution 里有没有 theoretical contribution？

---

### ACL / EMNLP / NAACL（NLP 顶会）

**核心关键词**：语言学分析、经验性结论、reproducibility

**Reviewer 偏好：**
- NLP 特有的 **linguistic analysis**：不只是刷性能，还要分析为什么方法在语言上有效
- 重视 **error analysis** 和 **case study**
- 重视数据集的多样性（多语言、多领域）
- ACL 系列的 reviewer 对 **writing quality** 本身也有要求

**ACL 特有机制：**
- **ARR（ACL Rolling Review）**：现在 ACL/EMNLP/NAACL 大多走 ARR 流程，评审结果可以 commit 到多个会议
- **Ethics review**：有专门的 ethics review 环节

**投稿 checklist：**
- [ ] 有没有 linguistic analysis（不只是数字，还要分析语言现象）？
- [ ] 有没有多语言实验（如果方法声称是 multilingual）？
- [ ] 有没有 limitations 节（ACL 系列明确要求）？
- [ ] 伦理声明是否填写？

---

### CVPR / ECCV / ICCV（CV 顶会）

**核心关键词**：可视化、效率、实际应用

**Reviewer 偏好：**
- 重视 **视觉展示**：demo、qualitative results、可视化分析
- 重视 **效率**：inference speed、parameter count、FLOPs
- 接受更多工程导向的贡献

**投稿 checklist：**
- [ ] Qualitative results 是否充分、清晰？
- [ ] 有没有和 SOTA 的效率对比（速度/参数量）？

---

## 读论文时：识别会议烙印

读一篇论文时，可以问自己：

1. **这篇论文的写法是不是在迎合某个会议的偏好？**
   - 公式密度很高 → 可能投 ICLR/ICML
   - Case study 很详细 → 可能投 ACL/EMNLP
   - 有 broader impact 节 → 可能投 NeurIPS

2. **这篇论文如果换个会议投，需要改什么？**
   这个视角能帮你理解各部分的写作动机。

3. **有没有明显针对 reviewer 文化的"讨好"写法？**
   比如 ICLR 论文在引言就放 theoretical guarantee，ACL 论文在方法之后立刻放 linguistic analysis。
