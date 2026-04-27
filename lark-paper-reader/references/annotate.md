# annotate.md — 注释层详细指南

本文档定义每类注释的**触发条件、格式和定位策略**。

---

## 优先级与数量原则

- **不要压缩信息**：callout 和 comment 是补充，不是替代原文
- **不要做段落总结式 callout**：callout 解释"为什么"，comment 概括"讲什么"
- **不做数字感知**（"这个分数好不好"）：留给读者判断
- 每篇论文预计：5-15 个 callout，10-20 个 comment

---

## Callout 块

### 📍 导读块（每篇论文仅一个，文档开头）

插入位置：标题/副标题的最后一个 block 之后

```xml
<callout emoji="📍" background-color="light-blue" border-color="blue">
<h3>导读指南</h3>
<p><b>核心问题：</b>一句话描述论文试图解决的问题</p>
<p><b>作者答案：</b>一句话描述核心方法和关键结论</p>
<h3>预备知识速查</h3>
<li><b>术语1</b>：简短定义（1-2句）</li>
<li><b>术语2</b>：简短定义</li>
</callout>
```

**不要**在导读块里加阅读路径——读者自己决定读哪里。

---

### 💡 公式推导 / 直觉解释

**触发时机**：每个有推导逻辑的公式段落之后，以及难以直觉理解的方法说明之后

内容要包含：
1. 每个符号的含义（用 `<li>` 列出）
2. 推导的逻辑链（"为什么这样推"，不只是"这个公式是什么"）
3. 一个直觉类比（可选，但对复杂公式很有效）
4. 与其他方法的关键区别（如果有）

```xml
<callout emoji="💡" background-color="light-yellow" border-color="yellow">
<h3>公式推导：<公式名称/编号></h3>
<li><b>符号1</b>：含义...</li>
<li><b>符号2</b>：含义...</li>
<p><b>推导逻辑：</b>步骤1 → 步骤2 → 结论</p>
<p><b>直觉：</b>类比解释...</p>
</callout>
```

---

### 📖 引用背景展开

**触发时机**：论文中**直接对比**或作为**理论基础**的重要引用首次出现时

用 `ph` 获取被引论文摘要/全文后生成内容：

```xml
<callout emoji="📖" background-color="light-green" border-color="green">
<h3>被引文献：<作者 年份> — <一句话定位></h3>
<p><b>论文：</b>标题</p>
<p><b>核心思路：</b>方法主体（2-3句）</p>
<p><b>与本文的关系：</b>本文扩展/对比/继承了什么</p>
</callout>
```

**只展开高价值引用**（在正文被引超过2次，或在实验对比中作为主要 baseline）。
一篇论文最多展开 3-5 篇参考文献，避免喧宾夺主。

---

### 🔧 实现要点

**触发时机**：方法论中有具体算法/训练循环描述时（每篇论文最多1-2个）

```xml
<callout emoji="🔧" background-color="light-orange" border-color="orange">
<h3>实现要点：<模块名></h3>
<p>一句话说明需要改动哪里</p>
<pre lang="python"><code>
# 关键代码片段（伪代码或 PyTorch 风格）
</code></pre>
<p><b>注意：</b>容易踩坑的地方...</p>
</callout>
```

---

### ❓ 读者常见疑问

**触发时机**：每个主要实验/消融节末尾（§ 实验、§ 消融）

内容来自：读这篇论文时，读者最可能在这里卡住的 2-3 个问题。
聚焦实验设计的合理性、超参选择的动机、与其他方法对比的公平性。

```xml
<callout emoji="❓" background-color="light-purple" border-color="purple">
<h3>读者常见疑问：<节名></h3>
<p><b>Q：问题1</b></p>
<p>A：回答...</p>
<p><b>Q：问题2</b></p>
<p>A：回答...</p>
</callout>
```

---

## Comment（行内评论）

### 格式要求

`--content` 必须是 JSON 字符串：
```python
content_json = json.dumps([{"type": "text", "text": "注释内容"}], ensure_ascii=False)
```

**不要**用 shell 直接拼 JSON（中文会有转义问题），统一用 Python subprocess 调用。

### 术语注释

**触发时机**：专业术语第一次在正文中出现

```python
# 用更唯一的上下文定位，避免 callout 中的相同词导致 ambiguous_match
selection = "利用Fisher信息矩阵（FIM）在局部极小值附近"  # 带上下文
note = "FIM 衡量参数对数据分布的敏感程度。对角元素近似为梯度平方的期望值..."
```

常见需要注释的术语类型：
- 数学工具（Hessian、Fisher、EMA、Jaccard）
- 领域概念（catastrophic forgetting、seesaw、PEFT）
- 论文特有缩写（第一次展开后的缩写版本不需要再注释）

### 段落摘要

**触发时机**：正文中超过 3 句的纯文字段落（无公式、无列表）

格式：`【段落摘要】一句话说明这段在讲什么`

```python
selection = "监督微调（SFT）已成为激活预训练大型语言模型（LLM）特定能力的主流范式"
note = "【段落摘要】引言第一段：交代背景——SFT 很成功，但多任务场景下共享参数导致任务间互相干扰。"
```

段落摘要放在段首（唯一定位文本为段落开头的前20-30个字），让读者扫读时能一眼判断是否需要细读。

---

## 定位策略（避免 ambiguous_match）

当 `selection-with-ellipsis` 报 `ambiguous_match` 时：

1. **换更长的上下文**：多包含几个字，直到唯一
2. **使用 `start...end` 语法**：`"段落开头...段落结尾"`
3. **用 `--block-id` 精确定位**：先 `docs +fetch --detail with-ids --scope keyword --keyword "..."` 拿 block_id，再 `block_insert_after`
4. **跳过**：如果定位实在困难（如数学公式段），降级为全文末尾 append，附上位置说明
