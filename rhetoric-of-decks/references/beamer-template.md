# Beamer 模板

Warm Professional 配色的完整 Beamer 模板。复制即用。

```latex
\documentclass[aspectratio=169,11pt]{beamer}

% --- 基础包 ---
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{xcolor}
\usepackage{ragged2e}
\usepackage{colortbl}
\usepackage{array}
\usepackage{hyperref}
\usepackage{adjustbox}

\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc,
                backgrounds, decorations.pathreplacing, shadows, fadings}
\pgfplotsset{compat=1.18}

% --- Warm Professional 配色 ---
\definecolor{DeepNavy}{HTML}{2E4057}
\definecolor{Teal}{HTML}{048A81}
\definecolor{WarmOrange}{HTML}{E85D04}
\definecolor{SoftPurple}{HTML}{9D4EDD}
\definecolor{WarmGray}{HTML}{6C757D}
\definecolor{LightGray}{HTML}{E9ECEF}
\definecolor{Cream}{HTML}{FBF8F1}
\definecolor{DeepRed}{HTML}{D62828}
\definecolor{Gold}{HTML}{D4A03A}
\definecolor{SoftWhite}{HTML}{FAFAFA}

% --- Beamer 颜色映射 ---
\setbeamercolor{normal text}{fg=DeepNavy, bg=SoftWhite}
\setbeamercolor{structure}{fg=DeepNavy}
\setbeamercolor{alerted text}{fg=DeepRed}
\setbeamercolor{example text}{fg=Teal}
\setbeamercolor{frametitle}{fg=DeepNavy, bg=SoftWhite}
\setbeamercolor{title}{fg=DeepNavy}
\setbeamercolor{subtitle}{fg=WarmGray}
\setbeamercolor{block title}{bg=DeepNavy, fg=SoftWhite}
\setbeamercolor{block body}{bg=LightGray, fg=DeepNavy}
\setbeamercolor{itemize item}{fg=WarmOrange}
\setbeamercolor{itemize subitem}{fg=Gold}

% --- 字体 ---
\usefonttheme{professionalfonts}
\setbeamerfont{title}{size=\huge, series=\bfseries}
\setbeamerfont{frametitle}{size=\Large, series=\bfseries}

% --- 去除多余元素 ---
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{headline}{}

% --- 极简页脚（仅页码） ---
\setbeamertemplate{footline}{%
    \hfill
    \begin{beamercolorbox}[wd=3cm,ht=2.5ex,dp=1ex,right,rightskip=0.6cm]{page number}
        \usebeamercolor[fg]{WarmGray}\scriptsize\insertframenumber
    \end{beamercolorbox}
    \vspace{0.3cm}
}

% --- 子弹样式 ---
\setbeamertemplate{itemize item}{\footnotesize\raisebox{0.3ex}{\tikz\fill[WarmOrange] (0,0) circle (0.45ex);}}
\setbeamertemplate{itemize subitem}{\footnotesize\raisebox{0.3ex}{\tikz\fill[Gold] (0,0) circle (0.35ex);}}

% --- 过渡页命令 ---
\newcommand{\transitionslide}[2]{%
    {\setbeamercolor{normal text}{fg=SoftWhite,bg=DeepNavy}
    \begin{frame}[plain]\vfill\begin{center}
        {\huge\bfseries\textcolor{Gold}{#1}}\\[0.6cm]
        {\large\textcolor{LightGray}{#2}}
    \end{center}\vfill\end{frame}}
}

\graphicspath{{figures/}}

% ============================================================
\begin{document}

% --- 标题页 ---
\begin{frame}[plain]
\vfill
\begin{center}
    {\huge\bfseries\textcolor{DeepNavy}{你的标题}}\\[0.4cm]
    {\large\textcolor{WarmGray}{副标题或一句话摘要}}\\[1cm]
    {\normalsize 作者名 \\ 机构 \\ \today}
\end{center}
\vfill
\end{frame}

% --- 开场：用一个惊人事实 ---
\begin{frame}{这里写一个论断式标题}
\vfill
\begin{center}
    {\fontsize{72}{84}\selectfont\textcolor{WarmOrange}{\textbf{47\%}}}\\[0.8cm]
    {\Large\textcolor{DeepNavy}{一句话解释这个数字的意义}}
\end{center}
\vfill
\end{frame}

% --- 过渡页示例 ---
\transitionslide{第一部分}{副标题说明}

% --- 内容 slide 示例 ---
\begin{frame}{处理组平均增加 61 英里}
% 注意：标题是论断，不是 "结果"
\vfill
\begin{center}
    % 这里放图表或关键数据
    \textcolor{WarmGray}{[图表或核心内容]}
\end{center}
\vfill
{\scriptsize\textcolor{WarmGray}{数据来源：XXX, 2025}}
\end{frame}

% --- 魔鬼辩护人 slide ---
\begin{frame}{最强反驳：选择偏差可能驱动结果}
\vfill
\begin{columns}[T]
\begin{column}{0.48\textwidth}
    \textcolor{DeepRed}{\textbf{质疑}}\\[0.3cm]
    参与者自选进入处理组，\\
    组间基线差异显著
\end{column}
\begin{column}{0.48\textwidth}
    \textcolor{Teal}{\textbf{回应}}\\[0.3cm]
    倾向得分匹配后结果稳健；\\
    安慰剂检验通过
\end{column}
\end{columns}
\vfill
\end{frame}

% --- 结尾：一句话要点 ---
\begin{frame}[plain]
\begin{tikzpicture}[remember picture,overlay]
    \fill[DeepNavy] (current page.south west) rectangle (current page.north east);
    \node[anchor=center,text=SoftWhite,font=\Large\bfseries,
          text width=0.8\paperwidth,align=center] at (current page.center)
        {明天他们还会记住的那一句话};
\end{tikzpicture}
\end{frame}

\end{document}
```

## 编译命令

```bash
# 标准编译（3 遍确保引用正确）
pdflatex -interaction=nonstopmode deck.tex
bibtex deck          # 如有引用
pdflatex -interaction=nonstopmode deck.tex
pdflatex -interaction=nonstopmode deck.tex

# 检查警告（目标：0 个）
grep -cE "Overfull|Underfull" deck.log
```

## 编译要求

**零警告**。每个 Overfull/Underfull 都必须修复：

| 警告 | 修复方法 |
|------|---------|
| Overfull hbox | 缩短文字、用 `\adjustbox`、表格加 `@{}` |
| Underfull hbox | 调整段落换行 |
| Overfull vbox | 拆分 slide、减少 `\vspace` |
| Underfull vbox | 加 `\vfill` 或调整间距 |
