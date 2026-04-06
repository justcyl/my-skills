# RevealJS / Quarto 模板

Warm Professional 配色的 Quarto RevealJS 幻灯片模板。复制即用。

## _quarto.yml

```yaml
project:
  type: default

format:
  revealjs:
    theme: [default, custom.scss]
    slide-number: true
    transition: fade
    transition-speed: fast
    width: 1600
    height: 900
    margin: 0.05
    center: true
    hash: true
    history: true
    code-overflow: wrap
    highlight-style: github
    self-contained: true
```

## custom.scss

```scss
/*-- Warm Professional for RevealJS --*/

$body-bg: #FAFAFA;
$body-color: #2E4057;
$link-color: #048A81;
$selection-background-color: #E85D04;

// 字号
$presentation-font-size-root: 24px;
$presentation-h1-font-size: 2.2em;
$presentation-h2-font-size: 1.6em;

section.has-dark-background {
  h2, h3, p { color: #FAFAFA; }
}

.reveal {
  h2 {
    color: #2E4057;
    font-weight: 700;
    border-bottom: 3px solid #D4A03A;
    padding-bottom: 0.2em;
  }

  strong { color: #E85D04; }
  em { color: #048A81; }
  code { color: #048A81; font-size: 0.85em; }

  blockquote {
    border-left: 4px solid #D4A03A;
    background: #E9ECEF;
    padding: 0.8em 1.2em;
    font-style: normal;
  }

  .slide-number { color: #6C757D; font-size: 0.6em; }

  // 过渡页
  .transition-slide {
    background: #2E4057;
    h2 { color: #D4A03A; border: none; }
    p { color: #E9ECEF; }
  }

  // 高亮框
  .highlight-box {
    background: linear-gradient(135deg, #048A81 0%, #2E4057 100%);
    color: white;
    padding: 1.5em;
    border-radius: 8px;
    text-align: center;
  }

  // 大数字
  .big-number {
    font-size: 4em;
    font-weight: 900;
    color: #E85D04;
    line-height: 1.1;
  }

  // 双栏对比
  .columns-contrast {
    display: flex;
    gap: 2em;
    .negative { border-left: 4px solid #D62828; padding-left: 1em; }
    .positive { border-left: 4px solid #048A81; padding-left: 1em; }
  }
}
```

## slides.qmd 模板

````markdown
---
title: "你的标题"
subtitle: "副标题或一句话摘要"
author: "作者名"
institute: "机构"
date: today
format: revealjs
---

## {background-color="#2E4057"}

::: {.highlight-box}
::: {.big-number}
47%
:::
一句话解释这个数字的意义
:::

::: {.notes}
这里写讲稿笔记，观众看不到
:::

---

## {.transition-slide background-color="#2E4057"}

第一部分

副标题说明

---

## 处理组平均增加 61 英里 {.scrollable}

<!-- 标题是论断，不是 "结果" -->

```{r}
#| echo: false
#| fig-width: 12
#| fig-height: 6
# 你的图表代码
```

::: {.footer}
数据来源：XXX, 2025
:::

---

## 最强反驳：选择偏差可能驱动结果

:::: {.columns}
::: {.column width="48%"}
**质疑** {style="color: #D62828;"}

参与者自选进入处理组，组间基线差异显著
:::

::: {.column width="48%"}
**回应** {style="color: #048A81;"}

倾向得分匹配后结果稳健；安慰剂检验通过
:::
::::

---

## {background-color="#2E4057"}

::: {style="color: #FAFAFA; font-size: 1.5em; font-weight: bold; text-align: center;"}
明天他们还会记住的那一句话
:::
````

## 渲染命令

```bash
quarto render slides.qmd
# 或实时预览
quarto preview slides.qmd
```

## Quarto 特有技巧

| 功能 | 语法 |
|------|------|
| 逐步揭示 | `::: {.incremental}` 或 `. . .` 分隔 |
| 讲稿笔记 | `::: {.notes}` |
| 代码高亮行 | `#| code-line-numbers: "2-3"` |
| 嵌入交互图 | 直接用 plotly / Observable |
| 多栏布局 | `:::: {.columns}` + `::: {.column}` |
| 背景图 | `## {background-image="bg.jpg"}` |
| Fragment 动画 | `::: {.fragment .fade-in}` |
