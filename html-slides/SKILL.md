---
name: html-slides
description: 单文件 HTML 幻灯片（Han Xiao 式固定舞台 deck）的制作方案。当需要做网页版 slides、HTML 幻灯片、会议演讲 deck、或希望用浏览器直接放映且导出 PDF 的演示文稿时使用。触发词："HTML slides""网页幻灯片""单文件 deck""hanxiao 风格 slides""做个网页版演讲稿"。
---

# html-slides

用一个手写的单文件 HTML 制作会议级演示文稿。方法源自 Han Xiao（Jina AI）的
公开演讲 deck（如 hanxiao.io/aie-sf-2026）：无框架、无构建步骤，浏览器直接
打开放映，Chrome 打印导出 PDF 交付会务。

## When To Use

- 需要视觉风格完全可控、能在线分享（一个 URL）的演讲 slides
- 需要图表标注与正文风格像素级统一（手写 SVG，而非图表库截图）
- 不适用：需要多人协作编辑的场景用 PPT/Slides；内容型交互网页用
  `interactive-html`；学术 beamer 需求用 `rhetoric-of-decks`

叙事与修辞（标题写论断、一张 slide 一个想法、三幕结构）遵循
`rhetoric-of-decks` 的原则，本 skill 只负责"HTML 这种载体怎么做"。

## 核心机制（不可省略的三件事）

1. **固定舞台 + 等比缩放**：`#stage` 固定 1280×720，所有排版用绝对 px；
   JS 按 `min(vw/1280, vh/720)` 缩放整个舞台。绝不写响应式断点——
   固定坐标系是排版永不破版的前提。
2. **设计 token + 语义组件**：颜色只在 `:root` 定义（主色/反派色/正面色
   三色体系）；每种修辞成分一个 class（金句、对比卡片、流程图、大数字、
   三线表……），slide 内不写内联颜色和字号。
3. **图表手写 SVG**：用 15 行工具箱（`el`/`txt`/`mount`）逐图绘制，
   数据放独立的 `data.js`。不用图表库——风格统一和图内结论性标注是
   这套方法的核心卖点。

完整机制拆解（导航、深链接、CSS 动画、打印适配、手机遥控）见
`references/anatomy.md`。

## Workflow

1. **大纲先行**：每张 slide 写一句论断式标题（不是"结果"而是"X 提升了
   61%"），排出三幕结构，**并按 `references/design-catalog.md` 的
   内容→组件决策表为每页标注版式**——纯文字版式（编号要点/定义列表/
   金句/引用）连续不超过 2 页，全 deck 至少 1/3 页面含图形组件。
   大纲连同版式标注一起与用户确认后再动手。
2. **起步模板**：复制 `assets/template.html` 到工作目录，重命名为
   `index.html`。模板内置 6 种版式（标题页/编号要点/对比卡片/流程图+
   大数字/SVG 折线图/金句结尾）。
3. **定设计 token**：优先从 `references/design-catalog.md` 的主题预设
   起步（默认 warm-cream 暖米+橙；另有 elastic-blue），或按用户品牌改
   `:root` 变量。保持三色语义：`--accent` 主角、`--foil` 反派/对照、
   `--teal` 次要正面。不要引入灰色文字——层级靠字号和字重区分。
4. **逐张生成 slide**：每张一个 `<section class="slide">`，只用语义组件
   拼装。缺组件时先看 `references/anatomy.md` 的组件清单，再考虑新写
   （新组件的样式也进 `<style>` 统一管理，不写内联）。
5. **图表**：先在 `references/design-catalog.md` 的配方库里选图型
   （折线/分组柱状/堆叠条/坡度图/热力图/散点/时间轴/盒线图）。数据写进
   `data.js`（`const DATA = {...}`），每图一个 `drawXxx()` 函数挂到对应
   容器 id。坐标轴刻度、单位、图内 legend、结论性标注（直接写在数据点旁）
   都要有；legend 放数据空白区，截图确认不与数据重叠。
6. **验证**：用 `scripts/screenshot.sh <file> <页码...>` 无头截图逐张检查
   溢出与对齐（内容超出 720px 高度是最常见问题）。有 figure-checker
   可用时交给它做视觉 QA。
7. **交付**：告知用户放映方式（浏览器打开，方向键翻页、`f` 全屏、
   点击左 1/3 后退右 2/3 前进、`#N` 跳页）；需要 PDF 时 Chrome 打印、
   纸张自定义 1280×720px、无边距。需要手机遥控翻页时按
   `references/anatomy.md` 的 sync 方案加装。

## 常见坑

- 字号低于 13px 在投影上不可读；正文不小于 16px
- 每张 slide 内容超出 720px 不会滚动，只会被裁掉——宁可拆页
- `@media print` 里必须关闭所有动画，否则 PDF 导出会截到中间帧
- MathJax 只在确有公式时引入（本地 vendor 文件，不走 CDN）
- `.kicker`/`.tag` 等 mono 标签常带 `text-transform:uppercase`，会把
  希腊字母 τ/π 转成大写破坏数学记号——含公式符号的标签要加
  `text-transform:none`
