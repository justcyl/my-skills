---
name: paper-format-check
description: AI/NLP 顶会论文格式自动检查。适用于"检查论文格式""投稿前检查""camera-ready 检查""帮我看看格式对不对"等请求。覆盖 NeurIPS、ICML、ICLR、ACL/ARR、EMNLP、AAAI 等会议的页数、匿名性、引用、字体嵌入、图表质量等格式要求，含 PDF 转图视觉审查。
---

# Paper Format Check

AI/NLP 顶会论文的投稿前/camera-ready 格式自动检查 skill。

## 何时使用

- 用户要投稿前检查论文格式
- 用户要准备 camera-ready 版本
- 用户问"格式对不对""会不会 desk reject"
- 用户指定了具体会议（NeurIPS、ACL 等）

## 使用前提

需要用户提供：
1. **PDF 文件路径**（已编译的论文）
2. **目标会议**（如 NeurIPS 2025、ACL 2025）
3. **论文类型**（long/short，投稿版/camera-ready）

如未指定会议，提示用户确认。不同会议规则差异很大。

## 会议格式速查

详见 `references/conference-rules.md`，以下是核心差异：

| 会议 | 正文页数（投稿） | 正文页数（camera-ready） | 审稿方式 | 模板 |
|------|-----------------|------------------------|---------|------|
| **NeurIPS** | 10 页（含图表，不含参考文献/附录） | 10 页 | 双盲 | `neurips_2025.sty` |
| **ICML** | 8 页（不含参考文献/impact statement/附录） | 9 页 | 双盲 | `icml2025.sty` |
| **ICLR** | 6-10 页（不含参考文献/附录）| 同投稿 | 双盲 | `iclr2025.sty` |
| **ACL/ARR** | Long 8 页 / Short 4 页（不含 limitations/参考文献） | +1 页 | 双盲 | `acl_latex.zip` |
| **EMNLP** | 同 ARR | +1 页 | 双盲 | 同 ARR |
| **AAAI** | 7 页（含图表参考文献）+ 2 页附加内容 | 同投稿 | 双盲 | `aaai25.sty` |

## 检查流程

### Phase 1: 元数据检查（自动化）

用 `pdfinfo` 和 `pdftotext` 提取信息后逐项检查：

```bash
# 1. 页数
pdfinfo paper.pdf | grep "Pages"

# 2. 纸张尺寸（应为 US Letter: 612 x 792 pts）
pdfinfo paper.pdf | grep "Page size"

# 3. 字体嵌入（camera-ready 必须全部嵌入）
pdffonts paper.pdf | grep -v "yes" | grep -v "^name"

# 4. PDF 元数据中的作者信息（双盲投稿不能有）
pdfinfo paper.pdf | grep -i "Author"
```

对每项输出判断 PASS / FAIL / WARN。

### Phase 2: 匿名性检查（双盲投稿版）

```bash
# 提取全文文本
pdftotext paper.pdf /tmp/paper-text.txt

# 检查常见去匿名化模式
grep -inE "our (previous|prior|earlier) (work|paper|study)" /tmp/paper-text.txt
grep -inE "university of|institute of|laboratory" /tmp/paper-text.txt
grep -inE "funded by|grant|support.*from" /tmp/paper-text.txt  # Acknowledgements
grep -inE "we (previously|earlier) (showed|proposed|demonstrated)" /tmp/paper-text.txt
grep -inE "available at https?://" /tmp/paper-text.txt  # 可追踪链接
grep -inE "anonymous|anonymized" /tmp/paper-text.txt  # 确认已匿名化
```

注意：
- ACL/ARR、EMNLP：**无匿名期要求**，但投稿版必须匿名
- ICML：允许 arXiv 预印，但投稿版不能引用非匿名版本
- ICLR：允许 arXiv，公开讨论在 OpenReview
- NeurIPS：允许 arXiv 预印

### Phase 3: 编译日志检查

```bash
# 致命错误
grep "^!" *.log

# Overfull/Underfull 警告
grep -cE "Overfull|Underfull" *.log

# 未定义引用
grep "Citation.*undefined" *.log
grep "Reference.*undefined" *.log

# 重复 label
grep "multiply defined" *.log

# 字体警告
grep -i "font" *.log | grep -i "warning"
```

所有致命错误和未定义引用必须为 0。Overfull 警告尽量为 0。

### Phase 4: 引用与参考文献检查

```bash
# 正文中的 [?] 未解析引用
grep -c "\[?\]" /tmp/paper-text.txt

# .bib 条目质量抽查（缺少关键字段）
# 检查是否有条目缺少 year/title/author
grep -c "@" references.bib  # 总条目数
```

人工/模型检查：
- 引用风格是否一致（编号 vs 作者-年份）
- 是否遵循会议要求的引用格式（ACL 用 `natbib`）
- 自引是否过多
- 近 3 个月内的论文可以不做详细对比（ARR 政策）

### Phase 5: 结构完整性检查

根据会议要求检查必需章节：

| 章节 | NeurIPS | ICML | ICLR | ACL/ARR | AAAI |
|------|---------|------|------|---------|------|
| Abstract | ✅ | ✅ | ✅ | ✅ | ✅ |
| Limitations | — | — | — | ✅ **必需** | — |
| Ethics/Broader Impact | 推荐 | ✅ **必需** | — | 推荐 | — |
| Responsible NLP Checklist | — | — | — | ✅ **必需** | — |
| Reproducibility | 推荐 | 推荐 | — | — | — |

```bash
# 检查 Limitations 章节（ACL/EMNLP 必需，缺失会 desk reject）
grep -ic "limitation" /tmp/paper-text.txt
```

### Phase 6: 视觉审查（默认关闭）

> **此步骤默认跳过**，仅在用户明确要求时启用（如「帮我看看视觉效果」「用视觉检查」「开启视觉审查」）。

启用后，PDF 转图由 Agent 逐页读取检查。

```bash
# 将 PDF 每页转为 JPEG（150 DPI + quality 85，平衡清晰度与 token 消耗）
mkdir -p /tmp/paper-review
pdftoppm -jpeg -jpegopt quality=85 -r 150 paper.pdf /tmp/paper-review/page
```

> **为什么是 150 DPI JPEG**：200 DPI PNG 每页约 100KB，150 DPI JPEG q85 每页约 50KB，体积减半，token 消耗显著降低，双栏论文的小字仍可读。不要用 100 DPI——双栏论文的脚注和图表标注会糊。

用 `read` 工具逐页读取图片，检查：

| 检查项 | 具体内容 |
|--------|---------|
| **边距** | 内容是否侵入页边距（模板定义的安全区域） |
| **图表可读性** | 图中文字是否可辨识、label 是否重叠 |
| **图表引用** | 是否每个图/表都在正文中被提及 |
| **Figure caption 位置** | 图的 caption 在下方，表的 caption 在上方 |
| **双栏对齐** | 两栏底部是否大致齐平（不要一栏长一栏短） |
| **字号一致性** | 正文、图注、脚注字号是否符合模板规范 |
| **色彩可辨识** | 图表在灰度下是否仍可区分 |
| **首页信息** | 投稿版无作者/机构；camera-ready 有完整作者信息 |
| **页码** | 投稿版通常有行号；camera-ready 通常无行号有页码 |

### Phase 7: 输出报告

生成结构化报告：

```markdown
# 论文格式检查报告

**目标会议**: [会议名]
**论文类型**: [投稿版 / camera-ready]
**检查时间**: [日期]

## 结果摘要

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 页数 | ✅ / ❌ | X 页（限制 Y 页） |
| 纸张尺寸 | ✅ / ❌ | |
| 字体嵌入 | ✅ / ❌ | |
| 匿名性 | ✅ / ⚠️ / ❌ | |
| 编译警告 | ✅ / ⚠️ | X 个 Overfull |
| 未定义引用 | ✅ / ❌ | |
| Limitations 章节 | ✅ / ❌ | |
| Ethics 章节 | ✅ / ⚠️ | |
| 视觉审查 | ✅ / ⚠️ | |

## ❌ 必须修复（会导致 desk reject）
## ⚠️ 建议修复
## ✅ 已通过
```

## 重要提醒

- **不同年份规则可能变化**——如果用户指定的年份与本 skill 记录的不同，先去官网确认最新 CFP
- **ICLR 2025 新增页数下限**（6 页最少），之前没有
- **ACL/ARR 的 Limitations 章节缺失 = desk reject**，这是硬性要求
- **ICML 的 Impact Statement 缺失 = desk reject**
- 页数计算方式各会不同（是否包含参考文献、附录、图表），务必按目标会议规则判断
