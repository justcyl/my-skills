---
name: interactive-html
description: 生成带数据嵌入、JS 交互的单文件离线 HTML 页面。当用户要求生成交互式网页、可视化数据浏览器、单文件 SPA、带侧边栏导航的展示页、Markdown 渲染器时触发。触发词："做一个网页"、"生成 HTML"、"交互式展示"、"可视化"、"数据浏览器"。
---

# 交互式 HTML 生成器

生成可直接用浏览器打开（`file://`）的单文件离线 HTML，包含数据嵌入、JS 交互和 Markdown 渲染。

## 核心判断：直接写 vs Python 脚本生成

| 场景 | 方式 |
|---|---|
| 内容静态、无大量数据（< 200 行）| 直接写 HTML |
| 数据从文件读取，或数据 > 50KB | **用 Python 脚本生成** |
| 内容含用户数据（代码/文档/Markdown）| **必须用 Python 脚本生成** |

> 用户数据中几乎肯定含有反引号、单引号、`</script>` 等危险字符，直接拼接必崩。Python 生成可以在写入前做统一转义。

## Python 脚本生成模式（推荐）

写一个 `gen_xxx.py`，数据处理和 HTML 模板分离，执行后输出 HTML 文件：

```python
import json
from pathlib import Path

# 1. 读取/处理数据
data = {...}

# 2. 序列化并转义（关键！）
data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

# 3. 拼接 HTML（JS 花括号全部双写）
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>...</head>
<body>
<!-- 数据独立存在 application/json 标签，安全隔离 -->
<script type="application/json" id="app-data">{data_json}</script>
<script>
const DATA = JSON.parse(document.getElementById('app-data').textContent);
// JS 的 {{ 和 }} 在 f-string 里需要双写
const keys = Object.keys(DATA);
</script>
</body>
</html>"""

Path("output.html").write_text(html, encoding="utf-8")
```

## 必须用的验证清单

每次生成后执行（见 `references/pitfalls.md` 了解每项原因）：

```bash
# 1. HTML 解析无错
python3 -c "
from html.parser import HTMLParser
c = HTMLParser(); c.feed(open('output.html').read())
print('HTML OK')
"

# 2. JS 语法无错（仅检查语法，不运行）
node --check <(python3 -c "
c = open('output.html').read()
js = c[c.rindex('<script>')+8:c.rindex('</script>')]
print('(function(){'); print(js); print('})()')
")

# 3. JSON 数据可解析
python3 -c "
import re, json
m = re.search(r'id=\"app-data\">(.*?)</script>', open('output.html').read(), re.DOTALL)
json.loads(m.group(1)); print('JSON OK')
"
```

## 布局选型

**浏览型内容**（用户需要选择 + 查看详情）→ **三栏无弹窗**：
```
[左栏: 列表/导航] [中栏: 卡片/筛选] [右栏: 详情直接显示]
```
点击即在右栏展示，不要弹窗。弹窗适合偶发操作，不适合连续浏览。

**文档/报告型内容** → **左侧固定导航 + 右侧滚动内容区**，section 切换用 JS show/hide。

**数据展示型** → 参考 `references/layouts.md`。

## 树形结构必须用 `<pre>`

```html
<!-- ❌ div 折叠空白，缩进消失 -->
<div>├── core/
│   └── file.py</div>

<!-- ✅ pre 保留所有空白 -->
<pre style="white-space: pre; font-family: monospace; line-height: 1.7;">
├── core/
│   └── file.py
</pre>
```

## onclick 不能嵌入内容字符串

```html
<!-- ❌ skill 内容含单引号就截断属性 -->
<div onclick='open({"desc":"it's broken"})'>

<!-- ✅ 只存索引，运行时从全局 DATA 查 -->
<div data-key="section-1" data-idx="0"
     onclick="openItem(this.dataset.key, +this.dataset.idx)">
```

## Markdown 渲染

用 CDN（离线可访问时）或内联 `marked.min.js`：
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
<script>
function renderMd(text) {
  return typeof marked !== 'undefined' ? marked.parse(text)
    : '<pre>' + text.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</pre>';
}
</script>
```

frontmatter 段单独用 `<pre class="fm-block">` 渲染，正文才走 `marked.parse()`。

## 文件大小控制

- 单次不写超过 ~1000 行；内容多时先写骨架 + 占位符，再用 `edit` 分段填充
- 嵌入大数据（> 500KB）时，HTML 体积通常 1–2MB，现代浏览器可接受
- 数据和 HTML 骨架分离（generator 脚本），数据变化时只需重跑脚本

## 详细踩坑说明

→ 见 `references/pitfalls.md`（`</script>` 截断、Python `\n` 陷阱、f-string 花括号冲突等 8 项完整说明）
