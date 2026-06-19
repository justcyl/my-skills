# Annotated Reader Layer For Codex

本文件只在 Annotated Reader Mode 或用户明确要求“注释/导读/背景/代码映射”时读取。目标是把解释层放到飞书文档的正确结构里：额外解释是 XML callout；边注是 Lark comment。不要把它们写成普通正文或 Markdown blockquote。

## 0. 子代理 / 并行要求

- Annotated Reader Mode 必须优先使用 Codex 当前可用的子代理/多代理工具生成候选：段落摘要、术语边注、公式直觉、视觉 QC。
- 若子代理/多代理工具可发现但工具规则要求用户显式授权，必须在继续生成论文文档前向用户请求授权；不得自行推断“用户未授权”并静默降级。
- 若用户拒绝授权、未在本轮授权，或当前环境确无可调用子代理工具，使用 Codex 本体分批处理，并在 `annotations.json` 与 `qc-report.md` 写明未启用子代理的具体原因。
- 子代理候选必须由主 agent 复核后再写入飞书；不要直接把候选原样灌入文档。

## 1. 5-PRE 扫描清单

创建飞书文档并插图后，先 fetch 文档内容，再建立 `annotation-plan.json`。清单至少包含：

- `formula_callouts`: 方法章节中需要解释的公式块，每项含 `anchor_text` 或 `block_id`、公式名、符号表、直觉。
- `method_examples`: 抽象方法步骤，每项含 anchor 与玩具例子。
- `reference_callouts`: 3 到 5 篇高价值引用，含 anchor 和展开内容。
- `question_callouts`: 高密度或隐含假设段落，含 anchor 与 Q/A。
- `term_comments`: 核心术语首次出现，含唯一定位文本与 1-2 句定义。
- `paragraph_comments`: 语义载荷高的段落，含段首定位文本与一句摘要。

处理时给每项维护 `status`: `pending | inserted | skipped`。`skipped` 必须写原因。

## 2. Callout 是原生 XML 块

callout 必须用 `docs +update --command block_insert_after` 或 `block_replace` 插入到对应 block 后。不能写进 `translated.md` 作为 `>` 引用块；不能放在文档末尾集中堆叠；不能混入原文翻译段落。

### 导读

```xml
<callout emoji="📍" background-color="light-blue" border-color="blue">
<h3>导读指南</h3>
<p><b>核心问题：</b>...</p>
<p><b>作者答案：</b>...</p>
<h3>预备知识速查</h3>
<li><b>术语</b>：解释。</li>
</callout>
```

### 公式直觉

方法章节每个关键公式块后都应插入 `💡`。内容必须包含符号、推导逻辑、直觉、与基线差异。

```xml
<callout emoji="💡" background-color="light-yellow" border-color="yellow">
<h3>公式直觉：FlowRL 目标</h3>
<li><b><latex>Z_\phi(x)</latex></b>：配分函数，估计 prompt 对应的总流量。</li>
<li><b><latex>w</latex></b>：裁剪后的轨迹级重要性权重。</li>
<p><b>推导逻辑：</b>先把奖励写成目标分布，再用轨迹平衡平方误差实现分布匹配。</p>
<p><b>直觉：</b>括号里的量是“当前策略给这条轨迹的流量”和“奖励分布要求的流量”之间的差。</p>
</callout>
```

### 具象化示例

```xml
<callout emoji="🌉" background-color="light-orange" border-color="orange">
<h3>具象化：奖励分布匹配</h3>
<p><b>论文说：</b>策略应匹配完整奖励分布，而不是只最大化最高奖励。</p>
<p><b>具体是这样的：</b>假设同一道题有三条有效解法，奖励分别为 1.0、0.8、0.7。</p>
<li>奖励最大化容易把概率集中到 1.0 那条路。</li>
<li>FlowRL 会让三条路按奖励权重都保留概率质量。</li>
<p><b>关键直觉：</b>多样性来自目标分布本身，而不是事后补一个鼓励分散的惩罚项。</p>
</callout>
```

### 引用、疑问、实现

沿用这些 emoji：

- `📖`：重要引用背景，插在该引用首次成为理论基础或 baseline 的位置。
- `❓`：读者常见疑问，插在高密度/隐含假设/可能争议段落后。
- `🔧`：实现要点或代码映射，代码块必须用 `<pre lang="python"><code>...</code></pre>` 放在 callout 内。

## 3. Comment 才是边注

边注必须通过 `lark-cli drive +add-comment` 写入，并锚定具体文本或 block。不要用 `--full-comment` 冒充边注，除非定位失败且 `qc-report.md` 明确记录。

推荐用 Python 生成 JSON，避免 shell 引号错误：

```python
import json, subprocess

DOC = "<document_id>"
selection = "反向 KL 散度之间的联系"
note = "【术语】反向 KL 指 D_KL(policy || target)，训练时只需从当前策略采样，但也更容易偏向目标分布的高概率区域。"
content_json = json.dumps([{"type": "text", "text": note}], ensure_ascii=False)

subprocess.run([
    "lark-cli", "drive", "+add-comment",
    "--doc", DOC, "--type", "docx",
    "--selection-with-ellipsis", selection,
    "--content", content_json,
    "--as", "user",
], check=False)
```

定位策略：

1. 先用术语首次出现或段落前 30 字作为 `selection-with-ellipsis`。
2. 歧义时用 `start...end` 扩大上下文。
3. 仍失败时 fetch with-ids，根据 block_id 加局部评论。
4. 只有局部定位失败时才允许全文评论，并在 QC 中记录。

## 4. 覆盖率要求

- 核心术语首次出现都要有 comment；论文专有术语、方法名、缩写、关键数学概念优先。
- 高语义载荷段落要有段落摘要 comment：包含设计决策、因果解释、量化发现、对比分析的段落都算。
- 常规 Annotated Reader 少于 8 条 comment 时需要解释原因；中长论文通常应有 12-25 条。
- 方法章节关键公式少于 2 个 `💡` callout 时需要解释原因。
- 至少 1 个 `🌉` 具象化示例、1 个 `❓` 读者疑问、3-5 个 `📖` 引用背景（若论文引用结构允许）。
