# 常用布局模式

## 三栏无弹窗（浏览型）

适合：数据浏览器、技能/文档查看器、任何"选择 + 查看"场景。

```
┌──────────┬────────────────┬───────────────────────────┐
│ 左栏     │ 中栏           │ 右栏                      │
│ 分类/导航 │ 筛选控件+卡片  │ 点击卡片后详情直接显示      │
│ 200px   │ 300px          │ flex-1                    │
└──────────┴────────────────┴───────────────────────────┘
```

```html
<body style="display:flex;height:100vh;overflow:hidden">
  <div id="col-nav"   style="width:200px;overflow-y:auto;border-right:1px solid #30363d">...</div>
  <div id="col-cards" style="width:300px;overflow-y:auto;border-right:1px solid #30363d;display:flex;flex-direction:column">
    <div id="filters" style="padding:10px;border-bottom:1px solid #30363d">...</div>
    <div id="card-list" style="flex:1;overflow-y:auto;padding:8px">...</div>
  </div>
  <div id="col-detail" style="flex:1;overflow-y:auto;padding:20px">
    <!-- 点击卡片后用 JS 更新此区域 -->
  </div>
</body>
```

**不要用 Modal 弹窗做详情**：弹窗适合"偶发操作"（确认删除、填表单），不适合"连续浏览"。

---

## 左导航 + 右内容（文档/报告型）

适合：多章节技术文档、分 section 的报告。

```
┌──────────┬────────────────────────────────────────────┐
│ 左侧导航  │ 主内容区（section 切换，同时只显示一个）      │
│ 固定     │ 可滚动                                      │
│ 260px   │ flex-1                                      │
└──────────┴────────────────────────────────────────────┘
```

```javascript
// section 切换：show/hide，不刷新页面
function show(id) {
  document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
  document.getElementById(id).style.display = 'block';
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`[data-id="${id}"]`).classList.add('active');
}
```

CSS 技巧：`.section { display: none }` + `.section.active { display: block }`，比 JS 操控 style 更易维护。

---

## 暗色主题 CSS 变量（直接复用）

```css
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
  --border: #30363d;
  --accent: #58a6ff;   /* 蓝：主要交互 */
  --accent2: #3fb950;  /* 绿：成功/正向 */
  --accent3: #f78166;  /* 红：错误/警告 */
  --accent4: #d2a679;  /* 橙：标注/代码 */
  --accent5: #bc8cff;  /* 紫：技能/分类 */
  --text: #e6edf3; --muted: #8b949e;
}
```

---

## 代码高亮

CDN 引入 Prism.js（支持 Python/Bash/TOML/Dockerfile）：

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
```

动态插入代码后需手动触发高亮：`Prism.highlightAll()` 或 `Prism.highlightElement(el)`。

---

## 大量数据的安全嵌入模板

```python
# gen_viewer.py — 数据与模板分离的标准模式
import json
from pathlib import Path

data = load_your_data()  # dict / list

# 关键：替换 </ 防止 HTML 解析器截断 script 标签
data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

html = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>数据浏览器</title>
</head>
<body>
<script type="application/json" id="app-data">""" + data_json + """\
</script>
<script>
const DATA = JSON.parse(document.getElementById('app-data').textContent);
// 从这里开始写 JS 逻辑，花括号不需要双写（不在 f-string 里）
</script>
</body>
</html>"""

Path("viewer.html").write_text(html, encoding="utf-8")
print(f"生成完成，大小: {Path('viewer.html').stat().st_size // 1024} KB")
```

注意：HTML 骨架用普通字符串拼接（`""" + data_json + """`），不用 f-string，避免 JS 花括号转义问题。只有包含 Python 变量插值的部分才用 f-string。
