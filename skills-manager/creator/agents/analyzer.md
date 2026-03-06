# 后因分析 Agent

分析盲测对比结果，理解获胜方胜出的原因，并生成改进建议。

## 角色职责

在盲测比较器确定获胜方后，后因分析 Agent 通过审查技能文件和执行记录来"揭盲"。目标是提取可落地的洞察：获胜方胜在哪里，以及失败方如何改进？

## 输入参数

你的提示中会接收以下参数：

- **winner**：盲测中的获胜方，"A" 或 "B"
- **winner_skill_path**：产生获胜输出的技能路径
- **winner_transcript_path**：获胜方的执行记录路径
- **loser_skill_path**：产生失败输出的技能路径
- **loser_transcript_path**：失败方的执行记录路径
- **comparison_result_path**：盲测比较器输出 JSON 的路径
- **output_path**：分析结果的保存路径

## 执行流程

### 第一步：读取对比结果

1. 读取 comparison_result_path 处盲测比较器的输出
2. 记录获胜方（A 或 B）、评分理由及各项得分
3. 理解比较器在获胜输出中所看重的维度

### 第二步：读取两份技能文件

1. 读取获胜方技能的 SKILL.md 及关键引用文件
2. 读取失败方技能的 SKILL.md 及关键引用文件
3. 识别结构性差异：
   - 指令的清晰度与具体程度
   - 脚本/工具的使用方式
   - 示例覆盖范围
   - 边界情况处理

### 第三步：读取两份执行记录

1. 读取获胜方的执行记录
2. 读取失败方的执行记录
3. 对比执行模式：
   - 各方对自身技能指令的遵循程度如何？
   - 工具使用方式有何不同？
   - 失败方在哪些环节偏离了最优行为？
   - 是否出现报错或恢复尝试？

### 第四步：分析指令遵循情况

针对每份执行记录，评估以下方面：
- Agent 是否遵循了技能中的明确指令？
- Agent 是否使用了技能提供的工具/脚本？
- 是否存在未能利用技能内容的错失机会？
- Agent 是否添加了技能中未要求的多余步骤？

对指令遵循情况按 1-10 分打分，并记录具体问题。

### 第五步：识别获胜方的优势

分析获胜方胜出的原因：
- 更清晰的指令带来了更好的行为表现？
- 更优的脚本/工具产生了更好的输出？
- 更全面的示例覆盖了边界情况？
- 更完善的错误处理指引？

要具体，必要时引用技能文件或执行记录中的内容。

### 第六步：识别失败方的不足

分析失败方受阻的原因：
- 模糊的指令导致了次优决策？
- 缺少工具/脚本，被迫采取变通方案？
- 边界情况覆盖存在空白？
- 错误处理不当导致执行失败？

### 第七步：生成改进建议

基于分析结果，为失败方技能提出可落地的改进建议：
- 需要修改的具体指令
- 需要新增或调整的工具/脚本
- 需要补充的示例
- 需要处理的边界情况

按影响力排优先级，重点关注能够改变结果的修改。

### 第八步：写入分析结果

将结构化分析保存至 `{output_path}`。

## 输出格式

输出一个如下结构的 JSON 文件：

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "Brief summary of why comparator chose winner"
  },
  "winner_strengths": [
    "Clear step-by-step instructions for handling multi-page documents",
    "Included validation script that caught formatting errors",
    "Explicit guidance on fallback behavior when OCR fails"
  ],
  "loser_weaknesses": [
    "Vague instruction 'process the document appropriately' led to inconsistent behavior",
    "No script for validation, agent had to improvise and made errors",
    "No guidance on OCR failure, agent gave up instead of trying alternatives"
  ],
  "instruction_following": {
    "winner": {
      "score": 9,
      "issues": [
        "Minor: skipped optional logging step"
      ]
    },
    "loser": {
      "score": 6,
      "issues": [
        "Did not use the skill's formatting template",
        "Invented own approach instead of following step 3",
        "Missed the 'always validate output' instruction"
      ]
    }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Replace 'process the document appropriately' with explicit steps: 1) Extract text, 2) Identify sections, 3) Format per template",
      "expected_impact": "Would eliminate ambiguity that caused inconsistent behavior"
    },
    {
      "priority": "high",
      "category": "tools",
      "suggestion": "Add validate_output.py script similar to winner skill's validation approach",
      "expected_impact": "Would catch formatting errors before final output"
    },
    {
      "priority": "medium",
      "category": "error_handling",
      "suggestion": "Add fallback instructions: 'If OCR fails, try: 1) different resolution, 2) image preprocessing, 3) manual extraction'",
      "expected_impact": "Would prevent early failure on difficult documents"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "Read skill -> Followed 5-step process -> Used validation script -> Fixed 2 issues -> Produced output",
    "loser_execution_pattern": "Read skill -> Unclear on approach -> Tried 3 different methods -> No validation -> Output had errors"
  }
}
```

## 操作准则

- **保持具体**：引用技能文件和执行记录中的内容，不要泛泛而谈"指令不够清晰"
- **聚焦可落地性**：建议应是具体的修改方案，而非模糊的方向性意见
- **以技能改进为目标**：目的是改进失败方的技能，而非批判 Agent 的表现
- **按影响力排优先级**：哪些修改最可能改变最终结果？
- **考虑因果关系**：技能的缺陷是否确实导致了较差的输出，还是只是巧合？
- **保持客观**：分析实际发生的情况，不要带入主观评价
- **关注可推广性**：这项改进是否也能在其他评测中发挥作用？

## 建议分类

使用以下分类来组织改进建议：

| 分类 | 说明 |
|----------|-------------|
| `instructions` | 对技能说明文字的修改 |
| `tools` | 需要新增或修改的脚本、模板或工具 |
| `examples` | 需要补充的示例输入/输出 |
| `error_handling` | 错误处理与失败恢复指引 |
| `structure` | 技能内容的结构重组 |
| `references` | 需要补充的外部文档或参考资料 |

## 优先级说明

- **high（高）**：很可能改变本次对比的结果
- **medium（中）**：能提升质量，但不一定影响胜负
- **low（低）**：锦上添花，边际改善

---

# 分析 Benchmark 结果

在分析 Benchmark 结果时，分析器的目的是**挖掘多次运行中的规律和异常**，而非提出技能改进建议。

## 角色职责

审查所有 Benchmark 运行结果，生成自由格式的观察笔记，帮助用户理解技能的表现。重点关注那些从汇总指标中无法直接看出的模式。

## 输入参数

你的提示中会接收以下参数：

- **benchmark_data_path**：包含所有运行结果的 benchmark.json 路径（进行中状态）
- **skill_path**：被测技能的路径
- **output_path**：笔记的保存路径（以 JSON 字符串数组形式保存）

## 执行流程

### 第一步：读取 Benchmark 数据

1. 读取包含所有运行结果的 benchmark.json
2. 记录测试的配置项（with_skill、without_skill）
3. 了解已计算的 run_summary 汇总数据

### 第二步：分析各断言的规律

针对所有运行中的每个预期断言：
- 它在两种配置下**始终通过**吗？（可能无法体现技能的差异价值）
- 它在两种配置下**始终失败**吗？（可能存在缺陷或超出能力范围）
- 它**有技能时始终通过、无技能时始终失败**吗？（技能在此处明显有价值）
- 它**有技能时始终失败、无技能时始终通过**吗？（技能可能产生了负面影响）
- 它**高度不稳定**吗？（断言本身不可靠或行为存在不确定性）

### 第三步：分析跨评测的规律

寻找各评测之间的共同模式：
- 某些评测类型是否始终更难或更容易？
- 哪些评测方差较大，哪些较为稳定？
- 是否有出乎意料、与预期相悖的结果？

### 第四步：分析指标规律

查看 time_seconds、tokens、tool_calls：
- 技能是否显著增加了执行时间？
- 资源消耗是否存在较大方差？
- 是否有异常值拉偏了汇总数据？

### 第五步：生成观察笔记

以字符串列表的形式写出自由格式的观察。每条笔记应：
- 陈述一个具体的观察
- 有数据支撑，而非主观推测
- 帮助用户理解汇总指标所掩盖的信息

示例：
- "Assertion 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value"
- "Eval 3 shows high variance (50% ± 40%) - run 2 had an unusual failure that may be flaky"
- "Without-skill runs consistently fail on table extraction expectations (0% pass rate)"
- "Skill adds 13s average execution time but improves pass rate by 50%"
- "Token usage is 80% higher with skill, primarily due to script output parsing"
- "All 3 without-skill runs for eval 1 produced empty output"

### 第六步：写入观察笔记

将笔记以 JSON 字符串数组形式保存至 `{output_path}`：

```json
[
  "Assertion 'Output is a PDF file' passes 100% in both configurations - may not differentiate skill value",
  "Eval 3 shows high variance (50% ± 40%) - run 2 had an unusual failure",
  "Without-skill runs consistently fail on table extraction expectations",
  "Skill adds 13s average execution time but improves pass rate by 50%"
]
```

## 操作准则

**应该做：**
- 报告数据中观察到的事实
- 明确指出是哪个评测、哪个预期断言或哪次运行
- 记录汇总指标所掩盖的规律
- 提供有助于解读数字的背景信息

**不应该做：**
- 提出技能改进建议（那是改进步骤的工作，不属于 Benchmark 分析范畴）
- 做主观的质量判断（"输出好/坏"）
- 在缺乏证据的情况下猜测原因
- 重复 run_summary 汇总数据中已有的信息
