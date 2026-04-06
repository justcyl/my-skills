# 配色方案参考

## 1. Warm Professional（默认推荐）

温暖、专业、适合大多数场景。

| 名称 | Hex | 用途 |
|------|-----|------|
| DeepNavy | `#2E4057` | 主文字、标题 |
| Teal | `#048A81` | 强调、示例 |
| WarmOrange | `#E85D04` | 警示、要点 |
| SoftPurple | `#9D4EDD` | 辅助强调 |
| WarmGray | `#6C757D` | 副标题、脚注 |
| LightGray | `#E9ECEF` | 背景块 |
| Cream | `#FBF8F1` | 备选背景 |
| DeepRed | `#D62828` | 警告、负面 |
| Gold | `#D4A03A` | 亮点、子弹点 |
| SoftWhite | `#FAFAFA` | 主背景 |

## 2. Academic Muted

低饱和度，适合严肃学术场景。

| 名称 | Hex | 用途 |
|------|-----|------|
| Charcoal | `#2D3436` | 主文字 |
| SlateBlue | `#4A6FA5` | 结构色 |
| Sage | `#6B9080` | 正面/示例 |
| Terracotta | `#C17767` | 强调 |
| Stone | `#8D8D8D` | 副文字 |
| Linen | `#F5F0EB` | 背景 |

## 3. High Contrast

高对比度，适合大教室投影。

| 名称 | Hex | 用途 |
|------|-----|------|
| Black | `#1A1A2E` | 主文字 |
| Electric Blue | `#0F3460` | 结构色 |
| Vivid Red | `#E94560` | 强调 |
| Pure White | `#FFFFFF` | 背景 |
| Silver | `#C4C4C4` | 辅助 |

## 选择指南

| 场景 | 推荐 |
|------|------|
| 学术研讨 / 会议报告 | Warm Professional 或 Academic Muted |
| 大教室教学 | High Contrast |
| 线上分享 / 屏幕阅读 | Warm Professional |
| 工作底稿 | 任意（内容重于形式） |

## CSS 变量（RevealJS / Quarto 用）

Warm Professional 的 CSS 变量版：

```css
:root {
  --r-main-color: #2E4057;
  --r-heading-color: #2E4057;
  --r-link-color: #048A81;
  --r-background-color: #FAFAFA;
  --r-selection-background-color: #E85D04;
  --r-selection-color: #FFFFFF;
  --r-main-font-size: 24px;
  --r-heading1-size: 2.2em;
  --r-heading2-size: 1.6em;
}

.reveal .slide-number { color: #6C757D; }
.reveal strong { color: #E85D04; }
.reveal code { color: #048A81; }
.reveal blockquote { border-left: 4px solid #D4A03A; }
```
