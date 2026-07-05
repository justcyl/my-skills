# 设计目录：主题预设 · 内容→组件决策表 · 图表配方库

配合 `anatomy.md`（机制拆解）使用。本文件回答三个问题：
用什么配色、这页内容该用什么组件、这份数据该画成什么图。

## 1. 主题预设

颜色只改 `:root`，组件全部自动换肤。三色语义不变：
`--accent` 主角 / `--foil` 反派或对照 / `--teal` 次要正面。

### warm-cream（默认推荐，Thinking Machines 风暖米+橙）

```css
:root{
  --bg:#FDFBF7;           /* 暖米色画布 */
  --ink:#221E1A;          /* 暖近黑墨色 */
  --accent:#D9480F;       /* 主角橙 */
  --accent-ink:#BC3E0C;   /* 小字号加深版 */
  --foil:#2563EB;         /* 反派/对照蓝 */
  --foil-ink:#1D4ED8;
  --teal:#0F766E;         /* 次要正面 */
  --accent-soft:#FBEADF;  /* 主色淡底：表格 hero 行 */
  --hair:rgba(34,30,26,.18); --hair2:rgba(34,30,26,.30);
}
```

### elastic-blue（范本原版，冷白+品牌蓝）

```css
:root{
  --bg:#FCFCFD; --ink:#1C1E23;
  --accent:#0B64DD;
  --foil:#F04E98; --foil-ink:#C2186A;
  --teal:#00BFB3; --teal-ink:#0A7B74;
  --accent-soft:#E7EEFC;
  --hair:rgba(28,30,35,.18); --hair2:rgba(28,30,35,.30);
}
```

自定义主题时的换肤检查单：

1. `--accent-soft` 必须是 `--accent` 的淡底版（表格 hero 行、高亮块用）
2. 小字号（<16px）颜色用 `-ink` 加深版，保证浅底对比度
3. `--hair/--hair2` 用 `--ink` 的低透明度版本，别用纯灰
4. 深色画布主题下 `.fbox.dark` 与页脚需反转检查一遍

## 2. 内容形态 → 组件决策表

**大纲阶段就为每页标注版式**（见 SKILL.md Workflow 第 1 步）。
拿到一页的内容先问"它的形态是什么"，再查表选组件：

| 内容形态 | 首选 | 备选 / 组合 |
|---------|------|------------|
| 单个核心论断 | `.takeaway` | + `.stats` 一个大数字压阵 |
| 数字型结论（1–4 个） | `.stats` 大数字 | 表格里加 `tr.hero` |
| 2–4 个方案对比 | `.cards` + `.hero` 卡 | 维度多时用 `table.bt` |
| 多维度多方案对比 | `table.bt` 三线表 | hero 行高亮我方 |
| 术语 / 要素定义 | `.deflist` | 项少时并成 `.cards` |
| 步骤 / 管线 / 闭环 | `.flow` + `.farr` | 有回路加 march 虚线动画 |
| 趋势 / 规模效应 | SVG 折线图（含 log 轴） | 外推段用虚线 |
| 多组 × 多指标 | SVG 分组柱状图 | 组多时拆两图 |
| 占比 / 构成 | SVG 堆叠条 | 不画饼图（角度难比较） |
| 前后两时点变化 | SVG 坡度图 slope | 两组柱状 |
| 矩阵 / 密度型数据 | SVG 热力图 | 可加涟漪动画（见 anatomy §6） |
| 两变量关系 / 前沿 | SVG 散点图 | 被淘汰点画墨色空心圆 |
| 历史 / 路线图 | SVG 水平时间轴 | `.nlist` 编号叙事 |
| 系统架构 | 手写 SVG 盒线图 | 简单时用 `.flow` |
| 引用权威 | `.pull` + `cite` | 关键词 `<strong>` 变主色 |
| 标签集合 / 选中态 | `.chip(.on)` | 常与图表同页做图例 |

### 非文字纪律（防"满屏 bullet"）

- 排大纲时统计版式：**纯文字版式（nlist / deflist / takeaway / pull）
  连续不超过 2 页**；全 deck 至少 1/3 的页面含图形组件
  （SVG 图表 / flow / cards / stats / 表格）
- 每个关键数字都问一遍"能不能画出来"——能画就不要只写在句子里
- 一页里"图 + 一句结论标题"优于"图 + 三条 bullet"

## 3. 图表配方库

全部基于 anatomy §5 的 15 行工具箱（`el`/`txt`/`mount`），
每图一个 `drawXxx()`，数据读 `data.js`。通用规则：

- 坐标轴、刻度、单位、图内 legend、**图内结论标注**缺一不可
- 图表配色同走三色 token，用 `getComputedStyle` 读取而不是写死 hex：
  `const CSSV=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();`
  换肤时图表自动跟随；数字用 `--mono` 字体
- `document.fonts.ready.then(renderAll)` 后再画，防量宽错误
- legend 放数据的空白区（画完截图确认不与数据/标注重叠）

### 折线图（趋势、scaling law）

```js
const X=v=>L+(Math.log10(v)-lgMin)/(lgMax-lgMin)*(W-L-R);  // log 轴
const Y=v=>H-B-(v-yMin)/(yMax-yMin)*(H-T-B);
// 实测段实线 stroke-width 3；外推段 stroke-dasharray:"7 6"
// 数据点 circle r=4.5；末端点旁直接标数值
```

要点：目标线用发丝横线+右端小字；两条线的语义色对应叙事立场
（我方 `--accent`，对照 `--foil`）。

### 分组柱状图（多阶段 × 多指标）

要点：组内柱间 6–8px、组间 ≥28px；柱顶标数值（mono 13px）；
结论标注放最有信息量的一组柱旁（如"行为修复，知识保留"）。

### 堆叠条 / 构成条

要点：横向堆叠条比饼图易读；每段内嵌白色/墨色百分比标签，
段太窄（<7%）时引线拉到条外标注。

### 坡度图 slope chart

要点：左右两列时点，每条线一个条目；上升 `--accent`、
下降 `--foil`、持平墨色；两端直接标条目名+数值，不用 legend。

### 热力图

要点：色阶只用主色透明度渐变（`--accent` 0.1→1.0），不引入新色相；
行列表头 mono 12–13px；可选涟漪动画（anatomy §6），打印时关闭。

### 散点图（关系、帕累托前沿）

要点：前沿线用主色加粗折线；被淘汰点墨色空心圆（不用灰色实心）；
个别关键点带名字标注，其余不标。

### 水平时间轴

要点：主轴发丝线，里程碑用主色圆点+上下交错的标签；
"现在"位置画主色竖线；未来段虚线。

### 架构 / 盒线图

要点：先试 `.flow` 组件够不够用；不够时手写 SVG——盒子
`rect rx=5` 墨色描边，关键节点填墨反白，连线带箭头 marker，
分层用发丝虚线框注 mono 小标签。
