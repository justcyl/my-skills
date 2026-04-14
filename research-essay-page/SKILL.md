---
name: research-essay-page
description: 生成 metauto.ai/neuralcomputer 风格的学术研究随笔 HTML 页面。多文件架构（CSS/JS 静态不动，agent 只生成内容 HTML）。支持封面图、多章节、对比表格、代码卡片（syntax highlight）、KaTeX 公式（颜色标注）、多类型边注（术语/符号/译注）、内联引用、BibTeX 引用块、可折叠摘要、story-aside callout、图片 lightbox。适用于：把论文/博客/技术随笔生成为精美 HTML 发布页面。
---

# Research Essay Page

将研究笔记、论文解读、技术随笔生成为精美 HTML 页面，风格参考 [metauto.ai/neuralcomputer](https://metauto.ai/neuralcomputer/index_cn.html)。

## 何时使用

- "把我的论文写成网页" / "生成博客页面" / "做个研究随笔网站"
- 需要 publication-quality HTML 页面用于发布/分享
- 将论文内容转为带设计感的 HTML，含图表、对比表、参考文献
- **论文解读**：不仅分析论文全文，还应检查 GitHub 官方实现，用代码卡片展示简化后的关键代码片段

## 核心设计偷好

1. **多文件架构优先**：CSS/JS 从 skill 目录复制，agent 只生成内容 HTML（通常 <40KB），避免大文件写入失败
2. **边注密集**：对关键名词、术语、符号、公式变量、翻译大量使用右侧边注，降低读者认知负荷
3. **代码即解读**：如果论文有 GitHub 实现，用 code-card 展示简化后的关键代码，帮助用户建立「论文→代码」的映射
4. **公式可视化**：用 KaTeX 渲染公式，用颜色标注解释公式各部分含义
5. **生成后必须 refine**：运行 `refine_check.py` 自动校验，迭代修复直到全部通过

## 模板文件

Skill 目录下有两套模板：

### 推荐：多文件架构（agent 只写内容）

| 文件 | 大小 | 说明 |
|------|------|------|
| `style.css` | ~2015 行 | **复制即用**，含所有组件样式 + 代码卡片 + 公式块 + 多类型边注 |
| `script.js` | ~536 行 | **复制即用**，lightbox + summary scroll + contact toggle |
| `index-template.html` | ~210 行 | **内容骨架**，agent 基于此生成，只有内容 HTML |

**工作流：** 复制 `style.css` + `script.js` → 基于 `index-template.html` 生成 `index.html` → 运行 refine_check

这样 agent 只需要写一个 <40KB 的内容文件。**`write` 工具单次上限约 15KB，内容 HTML 必须按 Step 4 的分片构建流程生成，禁止一次写入整个文件。**

### 备选：单文件架构（双击可开）

| 文件 | CSS 大小 | 适用场景 |
|------|----------|--------|
| `template-minimal.html` | ~1781 行 | 自包含单文件，含所有实用组件 |
| `template.html` | ~2676 行 | 完整版，含视频 demo gallery |

## 组件是否强耦合？

**不强耦合。** CSS 按命名空间严格分组，各组件互不依赖（除共享 CSS 变量外）。可以安全删除任意组件的 HTML 块，对应 CSS 不会影响其他部分。

### CSS 组件地图

```
组件                      CSS 行数   是否必须
─────────────────────────────────────────────
Core (布局+排版)           ~498      ✅ 必须
Route Compare Table       ~197      图表用
Figures (图片块)            ~76      图片用
Story Aside (callout)      ~99      ⚠️ 可选
Code Card (代码卡片)       ~120      🆕 代码展示用
Formula Block (公式块)     ~60       🆕 KaTeX 公式用
Enhanced Margin Notes      ~50       🆕 术语/符号/译注
Summary Block             ~94      ⚠️ 可选
Image Lightbox            ~237      图片放大用
Divider                     ~6      ✅ 必须
Contract Table             ~86      表格用
Citation Card              ~74      ⚠️ 可选
Page Footer                ~12      ✅ 必须
Media Queries             ~237      ✅ 必须
─────────────────────────────────────────────
style.css               ~2015 (多文件推荐)
```

如需进一步瘦身：删除对应 HTML 块，然后从 `<style>` 中注释掉对应 CSS 类即可。

## 使用流程（5 步）

### Step 1: 复制静态资源 + 读取模板

```bash
# 复制 CSS/JS（不需修改）
cp ~/.agents/skills/research-essay-page/style.css ./style.css
cp ~/.agents/skills/research-essay-page/script.js ./script.js
```

```python
# 读取内容模板
skill_dir = "~/.agents/skills/research-essay-page"
template_path = os.path.join(skill_dir, "index-template.html")
with open(os.path.expanduser(template_path)) as f:
    html = f.read()
```

### Step 2: 替换占位符

搜索所有 `{{` 找到待填内容：

```python
html = html.replace("{{TITLE}}", "你的标题")
html = html.replace("{{SUBTITLE}}", "TL;DR 一句话")
html = html.replace("{{AUTHOR_NAME}}", "作者名")
# ... 依次替换
```

### Step 3: 删除不需要的组件

直接删除对应 HTML 块，不影响其他部分：
- 无论文：删除 `<a class="title-link arxiv">`
- 无 GitHub：删除 `<a class="title-link github">`
- 无多语言：删除 `<a class="title-link translation">`
- 无联系方式：删除整个 `contact-toggle` + `contact-panel`
- 无封面图：删除 `<figure class="figure-block hero-figure">`
- 无 TL;DR：删除 `<div id="summary" ...>`
- 无引用：删除 `<section class="citation-card">`

### Step 4: 分片写入 + 构建

复制 `section` 块，按需规划章节。**每个章节写成独立的小 `.html` 片段文件，最后用 concat 脚本拼成 `index.html`**。写时无大小压力，产物仍是单文件可直接双击打开。

**目录结构**：
```
output/
  parts/
    00-head.html       # <!DOCTYPE html>...<body> 到 intro section 末尾的 <hr>
    01-intro.html      # intro section
    02-method.html     # method section（每章一个文件）
    03-experiments.html
    99-footer.html     # lightbox dialog + footer + 闭合标签
  style.css
  script.js
  index.html           # 由 concat 脚本生成，勿手动编辑
```

**各片段文件内容约定**：
- `00-head.html`：从 `<!DOCTYPE html>` 到 intro section 末尾的 `<hr class="divider">`
- `NN-chapterX.html`：`<!-- ══ §N ══ -->` 注释 + `<section>` 块 + 结尾 `<hr class="divider">`（最后一章不加 hr）
- `99-footer.html`：lightbox `<dialog>` + `<footer>` + `</article></div></main><script src="script.js"></script></body></html>`

每个片段用 `write` 工具直接写入，全部写完后运行 concat 脚本：

```bash
python3 -c "
import glob, os
files = sorted(glob.glob('parts/*.html'))
with open('index.html', 'w') as out:
    for f in files:
        with open(f) as fh:
            out.write(fh.read())
print(f'Done: {len(files)} parts → index.html')
"
```

**拼合后立即验证完整性：**
```bash
wc -l index.html                # 检查总行数
grep -c "<section" index.html   # 确认所有 section 都写进去了
grep "</html>" index.html       # 确认文件有正确结尾
```

### Step 5: Refine — 运行检查清单

生成初稿后，**必须**运行 `refine_check.py` 进行自动校验，根据失败项修复后重新检查，直到全部通过。

```bash
python3 ~/.agents/skills/research-essay-page/refine_check.py <output.html>
```

检查清单涵盖 6 大类、22+ 项检查：

| 类别 | 检查内容 |
|------|----------|
| **Structure** | 无残留占位符 `{{}}`、有且仅有 1 个 `<h1>`、≥2 section、lightbox dialog 存在、summary id 正确 |
| **Images** | 所有 `<img>` 有 alt 文本、CSS 含 `max-width: 100%`、`.with-margin-note` 不溢出 |
| **Tables** | 每张表列数一致（colspan 已展开计算）、至少有 1 张表 |
| **CSS Integrity** | 无 `.demo-gallery {` 嵌套 bug、无 `@media` 吞噬 bug、大括号配对平衡 |
| **Content** | 内联引用 `href="#ref-N"` 有对应 `id="ref-N"` 目标、无占位 URL、KaTeX 公式中无危险裸 `<` / `>` |
| **Accessibility** | `<html lang>` 存在、viewport meta、description meta |

**Refine 循环**：
1. 生成 HTML → 保存文件
2. 运行 `refine_check.py` → 查看 ❌ FAIL 项
3. 根据 `→` 提示修复 HTML
4. 重复 2–3，直到全部 ✅ PASS

---

## 已知模板陷阱（已在模板中修复）

以下是模板中曾存在的 CSS bug，`refine_check.py` 会自动检测它们。如果你从旧模板生成，需要手动修复：

| Bug | 症状 | 修复 |
|-----|------|------|
| `.demo-gallery {` 嵌套 | `.summary-block` 样式全部失效（TL;DR 不显示） | 删除 `.demo-gallery {` 这一行 |
| `@media (prefers-reduced-motion)` 未关闭 | lightbox 样式被吞进 media query，整个弹窗不工作 | 删除该 `@media` 行 |
| `.with-margin-note` 溢出 | `width: calc(100% + 176px)` 导致右侧内容被裁切 | 改为 `width: 100%; margin-right: 0;` |
| `<img>` 无 max-width | 远程大图片超出容器右边界 | 给 img 添加 `max-width: 100%; height: auto;` |
| KaTeX 公式里写裸 `<` / `>` | 浏览器会把例如 `$$m_k^{(<l)}$$` 中的 `<l` 当成 HTML 标签开头，导致 DOM 断裂、后续 section 被弹出 `<article>` | 在公式里改用 `\lt` / `\gt`；例如写成 `$$m_k^{(\lt l)}$$` |

### KaTeX 注意事项

- **禁止在 `$...$` 或 `$$...$$` 里直接写裸 `<` / `>`**。即使 KaTeX 语义上你想表达“小于 / 大于”，HTML 解析发生在 KaTeX 渲染之前，浏览器会先把 `<l`、`<div` 之类片段当成标签起始，直接破坏 DOM。
- **正确写法**：
  - 小于：`\lt`
  - 大于：`\gt`
- **会被误伤的典型例子**：
  - 错：`$$m_k^{(<l)}$$`
  - 对：`$$m_k^{(\lt l)}$$`
- `refine_check.py` 现在会专门检查这个问题；如果报错，优先把公式中的裸尖括号替换为 `\lt` / `\gt`。
- 该检查**不会**误报 `\left< ... \right>`、`\langle ... \rangle` 这类合法 LaTeX 用法。

---

## 组件 HTML 手册

### 章节 + 分割线
```html
<hr class="divider">
<section id="chapter-N">
    <h2>N. 章节标题</h2>
    <h3 class="minor-subhead">子节标题</h3>
    <p>正文段落，内联引用示例：<a class="inline-ref" href="#ref-1">[1]</a></p>
</section>
```

### 简单图片
```html
<figure class="figure-block plain-figure">
    <img src="path/to/image.png" alt="描述" loading="lazy" decoding="async">
    <figcaption>图注文字 <a href="#ref-1">[1]</a></figcaption>
</figure>
```

### 对比图卡（暖色渐变背景，可点击放大）
```html
<figure class="figure-block comparison-card">
    <a class="zoomable-image-link" href="path/to/fullsize.png">
        <img src="path/to/thumb.png" alt="描述" loading="lazy" decoding="async">
    </a>
    <figcaption>图注</figcaption>
</figure>
```
> `zoomable-image-link` 会自动接入 lightbox，`href` 指向原图

### 简单对比表（contract-table）
```html
<table class="contract-table">
    <thead>
        <tr><th>维度</th><th>方案 A</th><th>方案 B</th></tr>
    </thead>
    <tbody>
        <tr><td>速度</td><td>快</td><td>慢</td></tr>
        <tr class="spotlight-row"><!-- 高亮行 -->
            <td>精度</td><td>低</td><td>高</td>
        </tr>
    </tbody>
</table>
```

### 复杂分组对比表（route-compare-table）
```html
<div class="route-compare-block">
    <p class="route-compare-quickread"><strong>速读：</strong>一句话总结</p>
    <div class="route-compare-table-shell">
        <table class="route-compare-table">
            <thead><tr>
                <th>
                    <span class="route-compare-head-cn">维度</span>
                    <span class="route-compare-head-en">DIMENSION</span>
                </th>
                <th><span class="route-compare-head-cn">方案 A</span></th>
                <th><span class="route-compare-head-cn">方案 B</span></th>
            </tr></thead>
            <tbody>
                <tr class="route-compare-group-row"><td colspan="3">分组标签</td></tr>
                <tr class="route-compare-key-row">
                    <td>维度名</td><td>描述 A</td><td>描述 B</td>
                </tr>
            </tbody>
        </table>
    </div>
    <p class="route-compare-note"><strong>注：</strong>补充说明</p>
</div>
```

### Story Aside（callout/高亮框）
```html
<aside class="story-aside">
    <p class="story-aside-title">背景 / 注意 / 启示</p>
    <p>补充背景、提示或旁注内容。顶部有彩虹渐变装饰线。</p>
    <p>可有多段。</p>
</aside>
```

### 代码卡片（code-card）🆕
```html
<div class="code-card">
    <div class="code-card-header">
        <span class="code-card-filename">train.py</span>
        <span class="code-card-lang">Python</span>
    </div>
    <pre class="code-card-body"><code><span class="kw">def</span> <span class="fn">compute_advantage</span>(<span class="var">rewards</span>):
    <span class="cm"># RLOO leave-one-out baseline</span>
<span class="hl">    <span class="var">baseline</span> = <span class="var">rewards</span>.<span class="fn">mean</span>()</span>
    <span class="kw">return</span> <span class="var">rewards</span> - <span class="var">baseline</span></code></pre>
    <p class="code-card-caption">关键函数解说。<a href="https://github.com/...">源码 ↗</a></p>
</div>
```

**语法高亮 class**（Catppuccin Mocha 配色）：
| Class | 含义 | 颜色 |
|-------|------|------|
| `.kw` | 关键字 | 紫色 |
| `.fn` | 函数名 | 蓝色 |
| `.str` | 字符串 | 绿色 |
| `.num` | 数字 | 橙色 |
| `.cm` | 注释 | 灰色斜体 |
| `.var` | 变量/参数 | 红色 |
| `.typ` | 类型 | 黄色 |
| `.dec` | 装饰器 | 青色 |
| `.hl` | **高亮行** | 紫色背景 + 左侧条 |

> **code-card 使用建议**：不要照搬完整源码。简化为 10–20 行的关键逻辑，删掉 error handling、import、类型标注等噪音。用 `.hl` 高亮最核心的 1–3 行。

### 公式块（formula-block + KaTeX）🆕
```html
<!-- head 中需要 KaTeX CDN -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>

<!-- 公式块 -->
<div class="formula-block">
    $$\color{#2563eb}{\pi_\theta} \cdot \color{#dc2626}{r(s,a)} - \text{baseline}$$
    <div class="formula-legend">
        <span class="formula-legend-item"><span class="formula-legend-dot" style="background:#2563eb"></span> 策略</span>
        <span class="formula-legend-item"><span class="formula-legend-dot" style="background:#dc2626"></span> 奖励</span>
    </div>
</div>
```

**公式颜色约定**：
| CSS class | LaTeX 色值 | 含义 |
|-----------|-----------|------|
| `.fm-blue` | `#2563eb` | 策略/动作 |
| `.fm-red` | `#dc2626` | 奖励/损失 |
| `.fm-green` | `#16a34a` | 状态/上下文 |
| `.fm-purple` | `#9333ea` | 反思/元信息 |
| `.fm-orange` | `#ea580c` | 超参数 |

### 多类型边注 🆕
```html
<!-- 术语边注（蓝色） -->
<div class="with-margin-note">
    <div class="with-margin-note-main">
        <p>正文中提到 Meta-RL<span class="margin-note-marker marker-term">†</span> ...</p>
    </div>
    <span class="margin-note note-term">
        <span class="margin-note-index">†</span>
        <strong>Meta-RL</strong>：元强化学习，「学习如何学习」。
    </span>
</div>

<!-- 符号边注（紫色） -->
<span class="margin-note note-symbol">
    <span class="margin-note-index">α</span>
    $a_n$：第 n 个 episode 的完整搜索交互。
</span>

<!-- 译注（绿色，自动加「译」标签） -->
<span class="margin-note note-trans">
    <span class="margin-note-index">*</span>
    原文 "credit assignment"，直译为「信用分配」。
</span>
```

**边注类型**：
| class | marker class | 颜色 | 用途 |
|-------|-------------|------|------|
| `.note-term` | `.marker-term` | 蓝 | 术语/概念解释 |
| `.note-symbol` | `.marker-symbol` | 紫 | 符号/变量定义 |
| `.note-trans` | `.marker-trans` | 绿 | 翻译/译注（自动加「译」标签） |
| *(default)* | *(default)* | 红 | 一般备注 |

> **边注使用建议**：论文解读中大量使用边注，覆盖首次出现的每个专业术语、公式变量、英文术语的中文释义。目标是让非专业读者也能跟上。

### 可折叠摘要 TL;DR
```html
<!-- id 必须是 "summary"，JS 通过 id 绑定 -->
<div id="summary" class="summary-block is-collapsed" role="note" aria-label="TLDR">
    <div class="summary-header">
        <p class="summary-kicker">大致观点</p>
    </div>
    <ol class="summary-list">
        <li><div><strong>关键点 1</strong>：描述</div></li>
        <li><div>关键点 2</div></li>
    </ol>
</div>
```

### 带边注的段落
```html
<div class="with-margin-note">
    <div class="with-margin-note-main">
        <p>正文<span class="margin-note-marker">1</span>，继续...</p>
    </div>
    <span class="margin-note">
        <span class="margin-note-index">1</span>
        边注补充说明，字号更小，左侧有红色竖线。
    </span>
</div>
```

### 引用块（BibTeX）
```html
<section class="citation-card" id="citation">
    <h3 class="citation-title">引用</h3>
    <div class="bib-entry">
        <p class="bib-label">BibTeX</p>
        <pre class="bib-code">@misc{key2026,
  title   = {标题},
  author  = {作者},
  year    = {2026},
  url     = {https://...}
}</pre>
    </div>
    <h4 class="citation-subtitle">参考文献</h4>
    <ul class="reference-list">
        <li id="ref-1">[1] 作者. <a href="URL">论文标题</a>. 会议/期刊, 年份.</li>
        <li id="ref-2">[2] ...</li>
    </ul>
</section>
```

---

## 设计系统速查

### CSS 变量（在 `:root` 修改主题）
| 变量 | 默认值 | 含义 |
|------|--------|------|
| `--text` | `#1f2937` | 主文字色 |
| `--muted` | `#5b6474` | 次要文字色 |
| `--border` | `#e4e8ef` | 通用边框色 |
| `--accent` | `#1f3d63` | 强调色（链接） |
| `--content-width` | `895px` | 内容区最大宽度 |

### 字体栈
- **英文**：`"Iowan Old Style", "Baskerville", "Palatino Linotype", serif`
- **中文**：`"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"`
- **辅助 sans-serif**（meta/note 小字）：`"Avenir Next", "Segoe UI", sans-serif`

### 背景层次
1. 底色：`#fcfcfb`
2. 三个 radial-gradient（粉 8%、蓝 92%、绿 50%）- 柔和色晕
3. `repeating-linear-gradient` 网格线（`--grid: rgba(31,61,99,0.024)`）

---

## 重要约束

1. **生成后必须运行 `refine_check.py`**：这是 quality gate，不是可选步骤。它能捕获占位符残留、CSS bug、表格列不对齐等常见问题
2. **禁止用 `write` 工具一次写入完整 HTML**：`write` 单次上限 ~15KB，超出会被静默截断且不报错。典型论文解读页面 30–50KB，必须按 Step 4 的分片构建流程：每章节写成独立 `parts/NN-xxx.html`，最后 concat 拼合。
3. **lightbox dialog 不要删除**：即使没有可放大图片，也要保留 `<dialog id="image-lightbox">` 结构，JS 初始化会查找它
4. **`id="summary"` 不能改**：summary-block JS 通过此 id 绑定展开/折叠
5. **图片路径**：本地图片用相对路径，远程图片用完整 URL；`zoomable-image-link` 的 `href` 指向大图
6. **无外部依赖**：模板是完全自包含的 HTML，可直接双击打开

## 参考

- 原始示例：https://metauto.ai/neuralcomputer/index_cn.html
- 源码仓库：https://github.com/mczhuge/mczhuge.github.io/tree/main/neuralcomputer
- **多文件模板**：`index-template.html`（内容骨架）+ `style.css` + `script.js`
- 单文件模板：`template-minimal.html`（自包含）、`template.html`（含视频 demo）
- 质量检查：`refine_check.py` — 生成后必须运行的自动校验脚本（支持多文件/单文件两种模式）
