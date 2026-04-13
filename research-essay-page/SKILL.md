---
name: Research Essay Page
description: 生成 metauto.ai/neuralcomputer 风格的单文件学术研究随笔 HTML 页面。支持封面图、多章节、对比表格、内联引用、BibTeX 引用块、可折叠摘要、story-aside callout、图片 lightbox 等组件。适用于：把论文/博客/技术随笔生成为精美 HTML 发布页面。
---

# Research Essay Page

将研究笔记、论文解读、技术随笔生成为精美的单文件 HTML 页面，风格参考 [metauto.ai/neuralcomputer](https://metauto.ai/neuralcomputer/index_cn.html)。

## 何时使用

- 用户说"把我的论文写成网页""生成一个博客页面""做一个研究随笔网站"
- 需要生成 publication-quality 的 HTML 页面用于发布/分享
- 需要将 Markdown 内容或论文摘要转为带设计感的 HTML
- 需要展示论文、技术分析、研究综述，并带有图表、参考文献等学术组件

## 输出特点

- **单文件自包含**：所有 CSS 和 JS 内联，无需外部依赖，直接打开即可渲染
- **设计风格**：学术/编辑风，衬线字体，柔和渐变背景+网格线
- **响应式**：在移动端、平板、桌面均有良好表现
- **SEO 友好**：内置 Open Graph / Twitter Card meta tags
- **交互组件**：图片 lightbox、可折叠摘要、contact panel toggle

## 使用流程

### Step 1: 收集内容

向用户确认以下信息（可选，根据内容决定保留哪些组件）：

| 必填 | 可选 |
|------|------|
| 标题（`{{TITLE}}`） | arXiv 链接 |
| 副标题/一句话摘要（`{{SUBTITLE}}`） | GitHub 链接 |
| 作者名（`{{AUTHOR_NAME}}`） | 封面图 URL |
| 发布日期 | WeChat/Twitter 联系 |
| 章节标题与内容 | 参考文献列表 |

### Step 2: 从 template.html 开始

Skill 目录下的 `template.html` 是带完整 CSS+JS 的起始模板。

```bash
# 查看 template 位置
ls $(dirname $(find ~/.agents/skills -name "SKILL.md" | grep research-essay-page))/template.html
```

用以下 Python 读取模板后填充内容：

```python
with open("template.html", "r") as f:
    html = f.read()

html = html.replace("{{TITLE}}", "你的标题")
html = html.replace("{{SUBTITLE}}", "TL;DR 一句话")
# ... 替换所有 {{PLACEHOLDER}}

with open("output.html", "w") as f:
    f.write(html)
```

或直接编辑 HTML 文件，搜索 `{{` 找到所有需要替换的位置。

### Step 3: 填充内容

**必填占位符清单**（搜索 `{{` 一次性找到所有位置）：

```
{{LANG}}              - zh-CN 或 en
{{TITLE}}             - 页面标题（多次出现）
{{SUBTITLE}}          - 副标题/TL;DR
{{AUTHOR_NAME}}       - 作者名
{{META_DESCRIPTION}}  - SEO 描述（100-160 字符）
{{CANONICAL_URL}}     - 正式 URL
{{DATE_ISO}}          - 2026-04-13（ISO 格式）
{{DATE_DISPLAY}}      - 2026 年 4 月 13 日（显示格式）
{{LAST_UPDATED}}      - 同上

{{SITE_NAME}}         - 站点名
{{HOME_URL}}          - 首页链接
{{BLOG_URL}}          - 博客目录链接

{{HERO_IMAGE_URL}}    - 封面图 URL（无则删除 hero-figure 块）
{{HERO_IMAGE_ALT}}    - 封面图 alt 文本

{{CHAPTER_1_TITLE}}   - 第一章标题
{{CHAPTER_1_PARAGRAPH_1}} - 正文段落
...
```

**选填（删除对应 HTML 块即可）**：
- `{{ARXIV_URL}}` 无论文则删除 `.title-link.arxiv`
- `{{GITHUB_URL}}` 无代码则删除 `.title-link.github`
- `{{ALT_LANG_URL}}` 无多语言版本则删除 `.title-link.translation`
- `{{EMAIL}}`、`{{TWITTER_URL}}` 无联系方式则删除 `contact-panel`
- `{{OG_IMAGE_URL}}` 无封面图则删除 og:image meta

### Step 4: 添加自定义内容

按需使用以下组件（直接复制到对应章节）。

## 组件参考手册

### 章节分割线
```html
<hr class="divider">
```

### 内联引用
```html
文本内容<a class="inline-ref" href="#ref-1">[1]</a>，继续...
```

### 简单图片
```html
<figure class="figure-block plain-figure">
    <img src="path/to/image.png" alt="描述" loading="lazy" decoding="async">
    <figcaption>图注文字</figcaption>
</figure>
```

### 对比图卡片（带暖色渐变背景）
```html
<figure class="figure-block comparison-card">
    <a class="zoomable-image-link" href="path/to/fullsize.png">
        <img src="path/to/image.png" alt="描述" loading="lazy" decoding="async">
    </a>
    <figcaption>图注</figcaption>
</figure>
```

### 对比表格
```html
<table class="contract-table">
    <thead>
        <tr>
            <th>形态</th>
            <th>围绕什么组织</th>
            <th>主要职责</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>传统计算机</td>
            <td>显式程序</td>
            <td>稳定执行显式程序</td>
        </tr>
        <tr class="spotlight-row">  <!-- 高亮行 -->
            <td>Neural Computer</td>
            <td>Runtime</td>
            <td>让机器持续运行、沉淀能力</td>
        </tr>
    </tbody>
</table>
```

### Story Aside / Callout 框
```html
<aside class="story-aside">
    <p class="story-aside-title">背景</p>
    <p>这是一个侧边callout，顶部有彩虹渐变装饰线，用于补充背景知识或重要提示。</p>
</aside>
```

### 可折叠摘要块（TL;DR）
```html
<div id="summary" class="summary-block is-collapsed" role="note" aria-label="TLDR">
    <div class="summary-header">
        <p class="summary-kicker">大致观点</p>
    </div>
    <ol class="summary-list">
        <li><div><strong>关键点 1</strong>：描述...</div></li>
        <li><div>关键点 2</div></li>
    </ol>
</div>
```
> 注：需要 JS toggle 才能展开，`id="summary"` 与 JS 绑定，不要改 id。

### 带边注的段落
```html
<div class="with-margin-note">
    <div class="with-margin-note-main">
        <p>正文<span class="margin-note-marker">1</span>，更多内容...</p>
    </div>
    <span class="margin-note">
        <span class="margin-note-index">1</span>
        边注文字，对正文的补充说明。
    </span>
</div>
```

### 二级标题与子标题
```html
<h2>1. 章节标题</h2>           <!-- 章节级别 -->
<h3 class="minor-subhead">子标题</h3>  <!-- 小节 -->
```

### BibTeX 引用块
```html
<section class="citation-card" id="citation">
    <h3 class="citation-title">引用</h3>
    <div class="bib-entry">
        <p class="bib-label">arXiv BibTeX</p>
        <pre class="bib-code">@misc{key2026,
  title  = {标题},
  author = {作者},
  year   = {2026},
  url    = {https://arxiv.org/abs/...}
}</pre>
    </div>
    <h4 class="citation-subtitle">参考文献</h4>
    <ul class="reference-list">
        <li id="ref-1">[1] 作者. <a href="URL">论文标题</a>. 期刊/会议, 年份.</li>
    </ul>
</section>
```

### 视频 Demo 网格（可选，用于展示 demo）
```html
<div class="demo-grid general">
    <figure class="demo-shot" style="--shot-ratio: 0.743;">
        <div class="demo-shot-media">
            <video autoplay muted loop playsinline preload="none">
                <source src="path/to/demo.mp4" type="video/mp4">
            </video>
        </div>
        <figcaption>
            <strong>Demo 标题</strong>
            <span>描述文字</span>
        </figcaption>
    </figure>
</div>
```

## 设计系统

### CSS 变量（可在 `:root` 中修改主题色）
```css
:root {
    --text: #1f2937;              /* 主文字色 */
    --muted: #5b6474;             /* 次要文字色（eyebrow, figcaption） */
    --border: #e4e8ef;            /* 通用边框色 */
    --bg: #ffffff;                /* 白色背景 */
    --accent: #1f3d63;            /* 强调色（链接） */
    --grid: rgba(31, 61, 99, 0.024); /* 背景网格线颜色 */
    --content-width: 895px;       /* 内容区最大宽度 */
}
```

### 字体栈
- 正文（英文）：`"Iowan Old Style", "Baskerville", "Palatino Linotype", serif`
- 中文兜底：`"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"`

### 颜色主题
- 背景：`#fcfcfb`（近白）+ 多层渐变（粉/蓝/绿/紫）+ 网格线
- 标题色：`#111827`（深灰黑）
- 正文色：`#1f2937`
- 强调色：`#1f3d63`（深海蓝）
- Eyebrow/meta：`#5b6474`（中灰）

## 注意事项

1. **图片路径**：
   - 本地图片：相对路径（如 `assets/hero.png`）
   - 远程图片：完整 URL（如 `https://example.com/image.png`）
   - 不需要图片的组件直接删除对应的 `<figure>` 块

2. **lightbox 功能**：
   - 任何带 `class="zoomable-image-link"` 的 `<a>` 标签都会自动接入 lightbox
   - `href` 指向大图 URL
   - 必须保留 `<dialog class="image-lightbox" id="image-lightbox">` 结构

3. **删除不用的组件**：
   - 直接删除对应 HTML 块即可，CSS 不会影响未使用的样式
   - JS 是自发现的，不会因为缺少元素而报错

4. **多语言支持**：
   - `<html lang="zh-CN">` 或 `<html lang="en">`
   - `hreflang` 链接在 head 中添加

5. **SEO 最佳实践**：
   - `{{META_DESCRIPTION}}` 控制在 150 字符以内
   - 每个 `<img>` 都要有 `alt` 属性
   - 确保 `{{CANONICAL_URL}}` 填写正确

## 参考资源

- 原始示例页面：https://metauto.ai/neuralcomputer/index_cn.html
- 源码仓库：https://github.com/mczhuge/mczhuge.github.io/tree/main/neuralcomputer
- 本 skill 模板文件：`template.html`（同目录下）
