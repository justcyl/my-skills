---
name: research-essay-page
description: 生成 metauto.ai/neuralcomputer 风格的单文件学术研究随笔 HTML 页面。支持封面图、多章节、对比表格、内联引用、BibTeX 引用块、可折叠摘要、story-aside callout、图片 lightbox 等组件。适用于：把论文/博客/技术随笔生成为精美 HTML 发布页面。
---

# Research Essay Page

将研究笔记、论文解读、技术随笔生成为精美单文件 HTML 页面，风格参考 [metauto.ai/neuralcomputer](https://metauto.ai/neuralcomputer/index_cn.html)。

## 何时使用

- "把我的论文写成网页" / "生成博客页面" / "做个研究随笔网站"
- 需要 publication-quality HTML 页面用于发布/分享
- 将 Markdown 或论文内容转为带设计感的单文件 HTML
- 需要展示论文、技术分析、研究综述，含图表、对比表、参考文献

## 模板文件

Skill 目录下有两个模板：

| 文件 | CSS 大小 | 适用场景 |
|------|----------|---------|
| `template-minimal.html` | ~1781 行 | **推荐默认**，含所有实用组件，去掉了视频 demo gallery |
| `template.html` | ~2676 行 | 完整版，含视频 demo gallery |

**通常用 `template-minimal.html`**，除非需要展示多个视频 demo 网格。

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
Demo Gallery             ~847      ❌ 仅视频演示（默认已移除）
Summary Block             ~94      ⚠️ 可选
Image Lightbox            ~237      图片放大用
Divider                     ~6      ✅ 必须
Contract Table             ~86      表格用
Citation Card              ~74      ⚠️ 可选
Page Footer                ~12      ✅ 必须
Media Queries             ~237      ✅ 必须
─────────────────────────────────────────────
template-minimal.html    ~1781
template.html (全量)     ~2676
```

如需进一步瘦身：删除对应 HTML 块，然后从 `<style>` 中注释掉对应 CSS 类即可。

## 使用流程

### Step 1: 读取模板

```python
skill_dir = "~/.agents/skills/research-essay-page"
template_path = os.path.join(skill_dir, "template-minimal.html")
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

### Step 4: 添加章节内容

复制 `section` 块，按需添加/删除章节。

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

1. **lightbox dialog 不要删除**：即使没有可放大图片，也要保留 `<dialog id="image-lightbox">` 结构，JS 初始化会查找它
2. **`id="summary"` 不能改**：summary-block JS 通过此 id 绑定展开/折叠
3. **图片路径**：本地图片用相对路径，远程图片用完整 URL；`zoomable-image-link` 的 `href` 指向大图
4. **无外部依赖**：模板是完全自包含的 HTML，可直接双击打开

## 参考

- 原始示例：https://metauto.ai/neuralcomputer/index_cn.html
- 源码仓库：https://github.com/mczhuge/mczhuge.github.io/tree/main/neuralcomputer
- 模板文件：`template-minimal.html`（推荐）、`template.html`（含视频 demo）
