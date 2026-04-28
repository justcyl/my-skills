# formulas.md — 飞书公式渲染指南

飞书 `docs +create --doc-format markdown` 上传 Markdown 时**不渲染 LaTeX**——`$...$` 和 `$$...$$` 会以字面字符串写入文档。Step 3.5 的任务是把这些字面字符串替换为飞书原生 `<equation>` XML 块。

---

## 飞书公式 XML 语法

### 独立公式块（display equation）

```xml
<equation>\mathcal{P}(\mathcal{S};\pi_\theta,\mathcal{D})=\frac{1}{|\mathcal{D}|}\sum_{t\in\mathcal{D}}\mathbf{1}[\pi_\theta(t;\mathcal{S})=y_t^*]</equation>
```

### 行内公式（inline equation）

行内公式嵌套在 `<p>` 段落里，与文字交替出现：

```xml
<p>
  <text>对于每个任务 </text>
  <equation inline="true">p_i = \mathcal{A}^-(\mathcal{S}_0, \tau_i)</equation>
  <text>（若 </text>
  <equation inline="true">\tau_i \in T^-</equation>
  <text>），结果如下。</text>
</p>
```

---

## Step 2 翻译规则（不在此文件执行，确认 zh.md 格式正确）

翻译写入 zh.md 时：

- **独立公式**：单独成行，`$$` 开头、`$$` 结尾，前后空行
  ```
  （前段中文）
  
  $$\mathcal{L} = \frac{1}{N}\sum_{i=1}^N \ell(f(x_i), y_i)$$
  
  （后段中文）
  ```
- **行内公式**：保留 `$...$`，不转 Unicode 符号
  ```
  对每个样本 $x_i$，损失为 $\ell(f(x_i), y_i)$，总损失如公式(3)所示。
  ```
- **禁止**：把 `$p_i$` 写成 `p_i`，把 `$$\sum$$` 写成 `∑`。Unicode 符号无法被 Step 3.5 识别和替换。

---

## Step 3.5 完整脚本

### 前提

```bash
DOC=<document_id>
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user \
  > /tmp/lark_formula_pass.json
```

### Python 脚本

```python
#!/usr/bin/env python3
"""
formula_pass.py  <document_id>
扫描文档中所有 $$...$$ 独立块和含 $...$ 的段落，替换为 <equation> XML 块。
"""
import json, re, subprocess, sys

DOC = sys.argv[1]

with open('/tmp/lark_formula_pass.json') as f:
    doc_xml = json.load(f)['data']['document']['content']

replaced_block = 0
replaced_inline = 0
errors = []

# ── 1. 独立公式块 ──
# 上传 markdown 后，$$...$$ 独立行 → 一个 <p><text>$$...$$</text></p>
block_eq_re = re.compile(
    r'<p[^>]*id="(doxcn[^"]+)"[^>]*>\s*'
    r'(?:<text[^>]*>)?\s*\$\$\s*([\s\S]+?)\s*\$\$\s*(?:</text>)?\s*</p>',
    re.DOTALL
)

for m in block_eq_re.finditer(doc_xml):
    block_id = m.group(1)
    latex = m.group(2).strip()
    xml = f'<equation>{latex}</equation>'
    r = subprocess.run(
        ['lark-cli', 'docs', '+update', '--doc', DOC,
         '--command', 'block_replace', '--block-id', block_id,
         '--content', xml, '--doc-format', 'xml', '--as', 'user'],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        replaced_block += 1
        print(f'✓ block eq: {latex[:50]}')
    else:
        errors.append(f'block {block_id}: {r.stderr[:60]}')
        print(f'✗ block eq: {latex[:50]}')

# ── 2. 行内公式 ──
# 段落文字中含 $...$ → 拆分 text + equation inline + text
inline_para_re = re.compile(
    r'<p[^>]*id="(doxcn[^"]+)"[^>]*>\s*'
    r'<text[^>]*>([^<]*\$[^<]+\$[^<]*)</text>\s*</p>'
)

def build_inline_xml(raw_text):
    """把含 $...$ 的字符串拆成 <text>/<equation inline="true"> 交替结构"""
    parts = re.split(r'(?<!\$)\$(?!\$)((?:[^$]|\\.)+?)(?<!\$)\$(?!\$)', raw_text)
    inner = ''
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                inner += f'<text>{part}</text>'
        else:
            inner += f'<equation inline="true">{part}</equation>'
    return f'<p>{inner}</p>' if inner else None

for m in inline_para_re.finditer(doc_xml):
    block_id = m.group(1)
    raw_text = m.group(2)
    new_xml = build_inline_xml(raw_text)
    if not new_xml:
        continue
    r = subprocess.run(
        ['lark-cli', 'docs', '+update', '--doc', DOC,
         '--command', 'block_replace', '--block-id', block_id,
         '--content', new_xml, '--doc-format', 'xml', '--as', 'user'],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        replaced_inline += 1
        print(f'✓ inline eq: {raw_text[:50]}')
    else:
        errors.append(f'inline {block_id}: {r.stderr[:60]}')
        print(f'✗ inline eq: {raw_text[:50]}')

# ── 汇总 ──
print(f'\n替换完成：独立公式 {replaced_block} 个，行内公式段落 {replaced_inline} 个')
if errors:
    print(f'错误 {len(errors)} 个：')
    for e in errors:
        print(f'  {e}')
```

### 执行方式

```bash
python3 references/formulas_pass.py "$DOC"
# 或直接在 bash 里内联运行
```

---

## 注意事项

| 情况 | 处理方式 |
|------|---------|
| 段落中有多个 `$...$` | `build_inline_xml` 会逐个拆分，全部转为 `<equation inline>` |
| 嵌套 `$$` 和 `$` 在同一段落 | 先跑 block 替换，再跑 inline 替换，不会冲突 |
| LaTeX 中含 `<` `>` `&` | 替换前需转义：`<`→`&lt;`，`>`→`&gt;`，`&`→`&amp;` |
| 公式被翻译成 Unicode（如 `∑`, `π`） | **无法自动修复**，必须回溯 zh.md 改回 LaTeX 再重建文档 |
| MinerU full.md 里有图片形式的公式（截图） | 无法提取 LaTeX，只能保留原样或手动补写 |

---

## XML 转义辅助函数

```python
import html

def escape_latex(latex: str) -> str:
    """LaTeX 内容写入 XML 前转义特殊字符"""
    return html.escape(latex, quote=False)
```

在脚本中对 `latex` 调用 `escape_latex(latex)` 再放入 `<equation>` 标签。
