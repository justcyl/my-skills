# 交互式 HTML 踩坑详解

本文档记录生成交互式 HTML 时的常见错误及修复方案，按严重程度排序。

---

## 坑 1：`</script>` 截断脚本块（☠️ 最危险）

**现象**：页面渲染为乱文本，所有数据可见但 JS 不执行，按钮全部失效。

**原因**：用户数据（Markdown、代码片段）中含 `</script>` 字符串时，HTML 解析器提前关闭 `<script>` 标签，后续 JSON 数据变成普通 HTML 文本直接渲染。

**触发概率**：只要数据来自用户，几乎必然出现（d3.js 示例代码、HTML 示例文档等都含此字符串）。

**修复**：
```python
# 生成时替换 </ → <\/（JSON 合法转义，JSON.parse 能还原）
data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
```
```html
<!-- 用 application/json 标签存数据，HTML 解析器不处理其内容 -->
<script type="application/json" id="app-data">...data...</script>
<script>
  const DATA = JSON.parse(document.getElementById('app-data').textContent);
</script>
```

---

## 坑 2：onclick 属性含单引号崩溃（☠️ 很常见）

**现象**：点击按钮无反应，或触发错误的事件处理。

**原因**：`onclick='handler(${JSON.stringify(obj)})'` 中，如果 `obj` 的任意字段含单引号，会提前结束属性值。

```html
<!-- ❌ "it's broken" 里的 ' 截断属性 -->
<div onclick='open({"desc":"it's broken"})'>
```

**修复**：HTML 属性里只存安全的标量（数字 index、枚举 key），内容运行时从全局变量查：

```html
<!-- ✅ data-* 只存索引 -->
<div data-key="task-1" data-idx="2" onclick="openItem(this.dataset.key, +this.dataset.idx)">

<script>
function openItem(key, idx) {
  const item = DATA[key][idx];  // 从全局 DATA 安全读取
  // ...
}
</script>
```

---

## 坑 3：Python `\n` 在字符串里是真实换行符（🔥 难排查）

**现象**：JS 语法错误 "Invalid or unexpected token"，错误定位在字符串字面量内部。

**原因**：Python 的 `"""..."""` 不是 raw string，`\n` 会被解释为真实换行符。写入 HTML 后，JS 字符串字面量里出现断行，导致语法错误。

```python
# ❌ Python 字符串里 \n 是换行符
html = """    const end = content.indexOf("\n---", 3);"""
# 输出的 JS：
#     const end = content.indexOf("
# ---", 3);  ← 语法错误！

# ✅ 用 \\n，Python 解析后输出两字符 \n
html = """    const end = content.indexOf("\\n---", 3);"""
```

**排查方法**：`python3 -c "print(repr(your_string))"` 检查字符串实际内容，看 `\n` 是 `\\n`（正确）还是换行（错误）。

---

## 坑 4：f-string 与 JS 花括号冲突

**现象**：Python 报 `KeyError` 或 `ValueError: Single '}' encountered in format string`。

**原因**：f-string 把 `{` `}` 当插值符号，JS 代码里的对象字面量、模板字符串、解构赋值全部冲突。

```python
# ❌ Python 把 {method} 当变量，报 KeyError
html = f"const key = `{method}|{model}`;"

# ✅ JS 花括号全部双写
html = f"const key = `${{method}}|${{model}}`;"
```

**替代方案**：JS 代码量大时，改用 `.replace()` 替换少数几个占位符，不整体 f-string：

```python
JS_TEMPLATE = """
const IS_TRANSLATED = %IS_TRANSLATED%;
const DATA = JSON.parse(...);
"""
js = JS_TEMPLATE.replace("%IS_TRANSLATED%", "true")
```

---

## 坑 5：`<div>` 折叠空白，树形结构缩进消失

**现象**：文件树的缩进和 ASCII art 全部挤成一行。

**原因**：`<div>` 默认 `white-space: normal`，所有连续空格和换行折叠为一个空格。

```html
<!-- ❌ 全挤成一行 -->
<div>├── core/ │   └── file.py</div>

<!-- ✅ pre 保留所有空白 -->
<pre style="white-space: pre; font-family: 'SFMono-Regular', Consolas, monospace; line-height: 1.7;">
├── core/
│   └── file.py
</pre>
```

---

## 坑 6：output buffering 导致长时脚本无输出

**现象**：Python 脚本运行中 `tee` 日志文件一直为空，以为脚本挂了。

**原因**：Python 默认对管道输出做缓冲，`| tee` 时输出不会立即刷到文件。

**修复**：
```bash
python3 -u your_script.py | tee output.log   # -u 强制无缓冲
```
或在代码里所有 `print()` 加 `flush=True`：
```python
print("进度...", flush=True)
```

---

## 坑 7：翻译/生成脚本并发太高导致 API 变慢

**现象**：单个请求测试 8s，5线程并发后变成 71s/请求。

**原因**：API 服务对同一账号做并发限速，高并发反而降低总吞吐。

**经验值**：从 3 线程开始测，观察实际速率再调，通常 3–5 线程接近最优。

---

## 坑 8：浏览器静默吞错误，表现很奇怪

**现象**：按钮点不了、数据乱码，但浏览器 console 没有明显错误提示。

**原因**：HTML/JS 的某些错误（如 `</script>` 截断）不触发 JS 运行时错误，浏览器只是按破损的 DOM 渲染。

**排查工具**：

```bash
# HTML 结构验证
python3 -c "
from html.parser import HTMLParser
class C(HTMLParser):
    def __init__(self): super().__init__(); self.errs=[]
c=C(); c.feed(open('output.html').read())
print(f'</script> 出现 {open(\"output.html\").read().count(\"</script>\")} 次')
"

# JS 语法验证（node --check 只检查语法，不执行）
node --check <(python3 -c "
c = open('output.html').read()
js = c[c.rindex('<script>')+8:c.rindex('</script>')]
print('(function(){'); print(js); print('})()')
")

# JSON 数据验证
python3 -c "
import re, json
m = re.search(r'id=\"app-data\">(.*?)</script>', open('output.html').read(), re.DOTALL)
d = json.loads(m.group(1))
print(f'JSON OK: {len(d)} keys')
"
```
