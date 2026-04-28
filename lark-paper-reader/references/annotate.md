# annotate.md — 注释层详细指南

本文档定义每类注释的**触发条件、格式和定位策略**。

---

## 覆盖率硬性要求（必须逐元素执行，不可偷懒）

> ⚠️ 这些是**逐元素强制要求**，不是"预计数量"的上下限。论文短也好、公式多也好，每个元素都必须处理。

| 文档元素 | 必须有的注释 | 唯一例外 |
|----------|------------|---------|
| 方法章节中的每个公式块 | 💡 callout（符号含义 + 推导逻辑 + 直觉） | 纯符号定义行（如"其中 N 为 batch size"） |
| 每个抽象方法步骤/阶段描述 | 🌉 callout（具象化玩具示例） | 该步骤已有伪代码且流程清晰 |
| 每个专业术语首次出现 | comment（术语定义，1-2句） | 上文刚展开过同一术语的缩写 |
| 语义载荷 ≥2 分的段落（含因果解释/设计决策/量化发现/对比分析） | comment（段落摘要，由子代理预计算） | 纯过渡/引出/定义段落 |
| 语义密度高、读者可能困惑、或作者有言外之意的任意位置 | ❓ callout（读者常见疑问） | 无 |
| 每个被正文引用 ≥2 次或作为对比 baseline 的文献 | 📖 callout（引用背景） | 引用仅在 related work 泛列中出现 |
| 每个算法框 / 伪代码块 | 🔧 callout（含代码解读）| — |

**执行方式（Step 5 必须遵守）**：

```bash
# Step 5 开始前，先将 fetch 输出存文件，再处理（避免 pipe+heredoc stdin 冲突）
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user \
  > /tmp/lark_annotate_scan.json

python3 << 'EOF'
import json, re

with open('/tmp/lark_annotate_scan.json') as f:
    content = json.load(f)['data']['document']['content']

# 提取 h2/h3 节边界
sections = re.findall(r'<h[23][^>]*id="(doxcn[^"]+)"[^>]*>([^<]+)<', content)
print(f"章节: {len(sections)}")
for s in sections:
    print(f"  节 [{s[0]}]: {s[1]}")

# 提取长段落（>80字）
long_paras = re.findall(r'<p[^>]*id="(doxcn[^"]+)"[^>]*>(.{80,}?)</p>', content, re.DOTALL)
print(f"\n长段落: {len(long_paras)} 个（需逐一加 comment）")
for bid, text in long_paras[:5]:
    print(f"  [{bid}] {text[:50].strip()}...")
EOF
```

然后对每一类元素，**逐一**处理，处理完在心里打勾，不允许跳过。

---

## Callout 类型详解

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

**触发时机**：方法章节中每个公式块之后（见上表"唯一例外"）

内容要包含：
1. 每个符号的含义（用 `<li>` 列出，不遗漏）
2. 推导的逻辑链（"为什么这样推"，不只是"这个公式是什么"）
3. 直觉类比（对复杂公式必须有）
4. 与其他方法的关键区别（如果有）

```xml
<callout emoji="💡" background-color="light-yellow" border-color="yellow">
<h3>公式推导：<公式名称/编号></h3>
<li><b>符号1</b>：含义...</li>
<li><b>符号2</b>：含义...</li>
<p><b>推导逻辑：</b>步骤1 → 步骤2 → 结论</p>
<p><b>直觉：</b>用一个日常类比解释这个公式在做什么</p>
<p><b>为什么不用更简单的方案：</b>（可选）</p>
</callout>
```

---

### 🌉 具象化示例（抽象方法具体化）

**触发时机**：每当论文用抽象语言描述一个方法步骤时——即"告诉你发生了什么，但没有给具体例子"的段落。典型特征：
- 含 "we propose / we formulate / given ... we compute ..." 的方法描述
- 含 phase/stage/step 编号的流程描述
- 含"参数空间划分""记忆提取""策略更新"类抽象操作

**内容要求**：构造一个**最小玩具示例**，用具体数字/词语走一遍这个步骤：

```xml
<callout emoji="🌉" background-color="light-orange" border-color="orange">
<h3>具象化：<方法步骤名称></h3>
<p><b>论文说：</b>（引用原文的抽象描述，1句）</p>
<p><b>具体是这样的：</b></p>
<p>假设输入是 X，此时方法做了：</p>
<li>第1步：[具体操作，带假设数值]</li>
<li>第2步：[具体操作，带假设数值]</li>
<li>结果：[输出是什么，值是什么]</li>
<p><b>关键直觉：</b>为什么要这样设计，而不是更直接的做法？</p>
</callout>
```

**玩具示例的数值选择原则**：
- 用极小规模（如 vocab=5、dim=4、batch=2）让计算可以在脑中跟踪
- 若方法涉及比较/排序，显示排序前后的状态
- 若方法涉及概率/权重，用 [0.1, 0.3, 0.6] 这类清晰的数值，而非 0.xxx

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

### 🔧 实现要点（算法/代码）

**触发时机**：每个算法框/伪代码块之后，或来自 Step 5.5 的代码仓库

```xml
<callout emoji="🔧" background-color="light-gray" border-color="gray">
<h3>实现要点：<模块名></h3>
<p>一句话说明这段代码对应论文哪个公式/步骤。</p>
<pre lang="python"><code>
# 关键代码片段（伪代码或 PyTorch 风格）
# 每行关键操作必须有注释，说明对应论文中的什么
</code></pre>
<p><b>注意：</b>容易踩坑的地方...</p>
</callout>
```

---

### ❓ 读者常见疑问

**触发时机**：不限位置，以下任意情况都应插入：

| 情形 | 典型例子 |
|------|---------|
| 方法设计决策未给出理由 | "我们选择 K=10"——为什么是 10？ |
| 语义密度高、一句话包含多个跳跃 | "通过引入正则项，我们同时实现了…" |
| 作者有言外之意（隐含假设/限制） | 实验只在某一 benchmark 上验证时 |
| 读者看到结论可能产生"为什么"的自然反应 | 某方法在某任务上反而更差 |
| 方法对比不够公平或实验设置有争议 | 对比方法未使用相同的数据增强 |

内容来自：站在第一次读这篇论文的人的角度，提出 2-3 个最可能卡住的问题。

```xml
<callout emoji="❓" background-color="light-purple" border-color="purple">
<h3>读者疑问：<描述疑问的短语></h3>
<p><b>Q：问题1</b></p>
<p>A：回答（基于论文内容或合理推断）...</p>
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

**触发时机**：语义载荷 ≥2 分的段落——包含因果解释、设计决策、量化发现或对比分析的段落。纯过渡句、引出句、无分析的纯定义段落**不加摘要**。

段落摘要由 Step 2.5 的子代理批量预计算，主 agent 在 Step 5c 读取 JSON 批量写入，无需逐段手动判断。

评分标准详见 [`agents/paragraph-summarizer.prompt.md`](../agents/paragraph-summarizer.prompt.md)。

格式：`【段落摘要】含具体锚点的一句话`

```python
# 好的摘要（含具体锚点）
note = "【段落摘要】消融显示去掉参数隔离模块后 MMLU 下降 2.1 分，是最关键的设计选择"
# 差的摘要（空洞，会被子代理去重检查拒绝）
note = "【段落摘要】分析不同组件对结果的影响"
```

段落摘要放在段首（`para_start` 为开头前 30 字），让读者扫读时能一眼判断是否需要细读。

---

## 定位策略（避免 ambiguous_match）

当 `selection-with-ellipsis` 报 `ambiguous_match` 时：

1. **换更长的上下文**：多包含几个字，直到唯一
2. **使用 `start...end` 语法**：`"段落开头...段落结尾"`
3. **用 `--block-id` 精确定位**：先 `docs +fetch --detail with-ids --scope keyword --keyword "..."` 拿 block_id，再 `block_insert_after`
4. **跳过**：如果定位实在困难（如数学公式段），降级为全文末尾 append，附上位置说明
