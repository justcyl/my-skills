# 实验表格设计原则

## 源自 FAIR 的实验管理方法论

### 一、列（Columns）的设计——你关注什么

列的选择反映了你对研究问题的理解深度。

#### 必备列（Meta 信息）

| 列名 | 说明 |
|------|------|
| Exp ID | 唯一实验编号，格式如 `E001`，方便引用 |
| Date | 实验开始日期，用于追踪时间线 |
| Description | 一句话描述此实验与上一个实验的区别 |
| Hypothesis | 你认为这个实验为什么会 work（或不 work） |
| Prediction | 跑之前先预测结果（关键！），如"预计 acc 提升 1-2%" |
| Status | 状态：Planning / Running / Done / Failed / Abandoned |
| Config/Command | 可复现该实验的命令或配置文件路径 |

#### 实验变量列（Independent Variables）

这些列记录你主动改变的东西，是实验的自变量。根据实验类型不同：

- **Ablation**: 被移除/替换的组件
- **超参搜索**: 学习率、batch size、weight decay 等
- **架构对比**: 模型名称、层数、宽度等
- **方法对比**: 方法名称、关键区别

#### 结果列（Dependent Variables / Metrics）

核心原则：**只放你真正会看的指标**。指标太多等于没有指标。

建议不超过 5 个核心指标，外加 2-3 个辅助指标。

常见指标模板：
- **CV**: Top-1 Acc, Top-5 Acc, mAP, FLOPs, Params, Throughput
- **NLP**: PPL, BLEU, ROUGE-L, F1, Latency
- **RL**: Avg Return, Success Rate, Sample Efficiency
- **通用**: Train Loss, Val Loss, Best Epoch, Train Time

#### 分析列

| 列名 | 说明 |
|------|------|
| Δ vs Baseline | 与基线的差值（用公式自动计算） |
| Surprise? | 结果是否出乎意料（Yes/No），这是学习信号 |
| Insight | 从这个实验中学到了什么 |
| Next Action | 这个实验的结果驱动你做什么下一步 |

### 二、行（Rows）的设计——你做什么实验

行的编排体现了你的研究策略。

#### 核心原则：每一行都要和另一行形成对照

一个好的表格，任意相邻两行之间应该只有**一个变量**不同（理想情况）。这样才能产生清晰的因果信号。

#### 行的组织结构

```
Row 1: Baseline（基线，所有对比的锚点）
Row 2-4: 第一组 ablation（去掉组件 A / B / C）
Row 5-7: 第二组对比（不同的学习率）
Row 8-10: 在最佳配置上的进一步探索
...
```

#### 哪些实验不放进主表格

- 因 bug 导致的无效实验 → 删除或移到 "Failed" sheet
- 纯粹的 sanity check → 标记后隐藏
- 探索性的 "随便试试" → 放到 "Exploration" sheet，有价值再提升到主表

### 三、预测机制——表格的灵魂

凯明反复强调：**跑每个实验之前，你要预测结果。**

这不是占卜，而是检验你对系统理解的深度：

- **预测正确** → 你的心智模型（mental model）是对的，可以继续沿着这个方向推进
- **预测错误** → 这是一个 surprise，surprise 就是学习信号，说明你的理解有缺口，需要修正

#### 预测列的使用方式

1. 在 `Prediction` 列写下你的预期（如 "acc ≈ 78.5%"）
2. 跑完实验后，在 `Surprise?` 列标记是否出乎意料
3. 如果 Surprise = Yes，在 `Insight` 列写下你的分析

### 四、对照关系——梯度信号

表格的价值不在于单独的某一行，而在于**行与行之间的关系**。

好的表格设计应该让读者一眼就能看出：
- 哪些实验是一组对照
- 控制变量是什么
- 结果的变化趋势

可以用以下方式增强可读性：
- **分组着色**：同一组实验用相同底色
- **空行分隔**：不同组之间用空行区分
- **排序**：按实验变量值排序（如学习率从小到大）

### 五、Sheet 组织结构

一个完整的实验追踪工作簿应包含以下 Sheet：

| Sheet 名 | 用途 |
|----------|------|
| Dashboard | 高层概览：最佳结果、当前进度、关键发现 |
| Main Experiments | 主实验表格，所有正式实验 |
| Exploration | 探索性实验，信号不明确的放这里 |
| Failed / Abandoned | 失败的实验，保留以避免重复踩坑 |
| Config Log | 详细的超参配置记录 |
| Notes & Insights | 阶段性总结和关键洞察 |
