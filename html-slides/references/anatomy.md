# 单文件 HTML Deck 完整机制拆解

范本：https://hanxiao.io/aie-sf-2026/ （30 张 slide，约 110KB index.html）。
文件构成：`index.html`（全部 HTML+CSS+JS）+ `data.js`（图表数据）+
`sync.js`（手机遥控，可选）+ `vendor/tex-svg.js`（本地 MathJax，可选）。

## 1. 固定舞台 + 等比缩放

```css
html,body{height:100%;background:#0b0a08;}   /* 舞台外围深色，像放映厅 */
body{overflow:hidden;}
#stage{position:fixed;left:50%;top:50%;width:1280px;height:720px;
  transform:translate(-50%,-50%);transform-origin:center center;
  background:var(--bg);overflow:hidden;}
.slide{position:absolute;inset:0;display:none;flex-direction:column;
  padding:62px 76px 58px;}
.slide.active{display:flex}
```

```js
function fit(){
  // in-app webview（微信/LinkedIn）首次加载可能报 0 尺寸，逐级回退且永不缩放到 0
  const vv=window.visualViewport;
  const w=(vv&&vv.width)||innerWidth||document.documentElement.clientWidth||1280;
  const h=(vv&&vv.height)||innerHeight||document.documentElement.clientHeight||720;
  let s=Math.min(w/1280,h/720); if(!(s>0))s=1;
  stage.style.transform=`translate(-50%,-50%) scale(${s})`;
}
['resize','orientationchange','load','pageshow'].forEach(ev=>addEventListener(ev,fit));
if(window.visualViewport)visualViewport.addEventListener('resize',fit);
// 应对晚到的 viewport 尺寸（in-app webview 不可靠）
[60,160,320,650,1200].forEach(t=>setTimeout(fit,t));
```

为什么不做响应式：slide 是空间排版艺术，元素间的相对位置就是信息。
固定 1280×720 坐标系让设计所见即投影所得，字号间距全部用 px 绝对值。

## 2. 导航（约 30 行）

```js
function show(n){
  i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>s.classList.toggle('active',k===i));
  pg.textContent=(i+1)+' / '+slides.length;
  footEl.classList.toggle('hidden', i===0||i===slides.length-1);  // 首尾页藏页脚
  if(location.hash!=='#'+(i+1)) history.replaceState(null,'','#'+(i+1));
}
```

- 键盘：`→ ↓ 空格 PageDown` 前进，`← ↑ PageUp` 后退，`Home/End` 首尾，
  `f` 全屏
- 点击：屏幕左 1/3 后退、右 2/3 前进（讲台上单手可用）
- `#N` hash 深链接：刷新停在当前页，也可直接分享某一页

## 3. 设计 token 与三色体系

```css
:root{
  --bg:#FCFCFD; --ink:#1C1E23;      /* 近白画布 + 近黑墨色 */
  --accent:#0B64DD;                  /* 主角色：结构、hero、正确路线 */
  --foil:#F04E98; --foil-ink:#C2186A;/* 反派色：失败/对照组（小字用加深版保对比度）*/
  --teal:#00BFB3; --teal-ink:#0A7B74;/* 次要正面色 */
  --accent-soft:#E7EEFC;             /* 主色淡底，高亮表格行 */
  --hair:rgba(28,30,35,.18); --hair2:rgba(28,30,35,.30);  /* 发丝线 */
}
```

设计纪律（来自范本注释）：
- **no grey**——次级文字不用灰色，同一墨色靠字号/字重区分层级
- 颜色有叙事角色：蓝=我们的方案，粉=对照/失败路线，青=中性正面。
  整个 deck 保持一致，观众看到颜色就知道立场
- 小字号（<16px）用加深版颜色（`--foil-ink`），保证近白底上的对比度

## 4. 语义组件清单

每种"修辞成分"一个 class，slide 内只拼组件不写内联样式：

| 组件 | class | 用途 |
|------|-------|------|
| kicker | `.kicker` | 顶部 mono 小标签，`::before` 画一段主色短横线 |
| 主标题 | `h1` / `.h-slide` | 60px 标题页 / 35px 内容页，负字距 |
| 金句 | `.takeaway` | 居中加粗一两行，`text-wrap:balance`，每页至多一句 |
| 引用 | `.pull` + `cite` | 左侧 4px 主色边，关键词 `<strong>` 变主色 |
| 编号要点 | `.nlist/.nitem` | mono 大编号 + 标题 + 小字说明 |
| 定义列表 | `.deflist/.defrow` | 左列 mono 标签（主色左边线）+ 右列描述 |
| 对比卡片 | `.cards/.card(.hero)` | hero 卡 `box-shadow:0 0 0 1px var(--accent)` 双描边 |
| 流程图 | `.flow/.fbox(.dark)/.farr` | 墨色描边盒 + 主色箭头，关键节点反白 |
| 大数字 | `.stats/.stat .v(.o/.foil)` | 46–62px mono 数字 + 小字标签 |
| 三线表 | `table.bt` | `tabular-nums` 对齐，`tr.hero` 淡蓝底高亮行 |
| chip | `.chip(.on)` | 圆角胶囊标签，选中态墨底反白 |
| 页脚 | `#chrome` | 左标题右页码，发丝线上边框，首尾页隐藏 |

## 5. 手写 SVG 图表

工具箱（全部约 15 行）：

```js
const SVGNS='http://www.w3.org/2000/svg';
function el(t,a){const e=document.createElementNS(SVGNS,t);
  for(const k in a)e.setAttribute(k,a[k]);return e;}
function txt(x,y,s,o={}){/* text 元素：fs/fw/fill/anchor/mono */}
function mount(id,w,h){/* 容器内建 svg，viewBox 定坐标系，preserveAspectRatio */}
```

每张图一个 `drawXxx()`：手动写 `X()/Y()` 比例尺（含 log 轴就 `Math.log10`）、
坐标轴线、刻度、轴标题（rotate(-90) 的 y 轴标签）、数据元素、图内 legend。
数据一律从 `data.js` 的 `DATA` 对象读，改数据不碰绘图代码。

值得抄的细节：
- **结论标注画进图里**：如 "the in-domain win does not transfer" 直接放在
  数据空白区，观众不用对照图例推理
- 被淘汰的点用墨色空心圆（不用灰色实心），前沿线用反派色加粗
- 字体与正文同源（sans 正文 / mono 数字），图表和 slide 无风格断层
- 渲染时机：`document.fonts.ready.then(renderAll)` 防字体未载入时量宽错误

## 6. CSS 动画（少量、有含义、可打印）

- 反馈回路箭头：`stroke-dasharray:6 5` + `@keyframes march{to{stroke-dashoffset:-28}}`
  跑马灯，示意"循环"
- 热力图对角波浪：每格 `animationDelay = 符号相位 + 列*60ms + 行*40ms`，
  正负值错开半个周期，形成绿/红交替涟漪
- `@media print{*{animation:none!important}}`——PDF 导出不能截到中间帧

## 7. 公式（可选）

MathJax 3 本地文件（`vendor/tex-svg.js`，不走 CDN 保证离线可放映）：

```html
<script>
window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},
  svg:{fontCache:'none'},options:{enableMenu:false}};
</script>
```

## 8. 手机遥控翻页（可选，sync.js）

投影端打开 `?follow`，手机端做 controller。零后端方案：页码消息同时发到
多条免费公共通道，接收端"最新时间戳获胜"，任一通道活着就能工作：

1. **ntfy.sh**：HTTP POST 发布 + SSE 订阅（主通道，无需注册）
2. **EMQX 公共 broker**：MQTT over WSS（备份，mqtt.js 懒加载）
3. 自建 Cloudflare Worker（可选第三通道）

防冲突：每个 controller 会话持一个 epoch（取 `Date.now()`），follower 锁定
最大 epoch；旧 controller 静默 20s 后允许接管，防止遗留手机标签页干扰投影。
topic 用长随机后缀（如 `deck-slug-7q3m9k2x`）防碰撞。

## 9. 交付形态

- **放映**：任何浏览器打开 `index.html`（或部署到静态托管），`f` 全屏
- **PDF**：Chrome 打印 → 纸张自定义 1280×720px、无边距、背景图形勾选
- **分享**：静态托管后一个 URL 即全部；`#N` 可直链任意一页
