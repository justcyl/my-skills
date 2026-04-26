# 格式检查（format-check）

投稿前 / camera-ready 的论文格式检查。分两层：

| 层 | 工具 | 说明 |
|----|------|------|
| **硬规则自动检查** | `scripts/check_hard_rules.sh` | 完全可机器判断的 PASS/FAIL 规则，秒级完成 |
| **视觉审查** | pi-subagent figure-qa（可选） | 逐页视觉 QA，需用户明确要求 |

---

## 使用前提

- **PDF 文件路径**（已编译的论文）
- **目标会议**（neurips / icml / iclr / acl / emnlp / aaai）
- **论文类型**（submission / camera-ready）
- 依赖工具：`pdfinfo`、`pdffonts`、`pdftotext`（`brew install poppler`）

---

## 硬规则自动检查

运行脚本，一次性覆盖所有可机器判断的硬规则：

```bash
bash ~/.agents/skills/academic-paper/scripts/check_hard_rules.sh \
  paper.pdf <conference> <submission|camera-ready> [OPTIONS]

# 示例：ACL long paper 投稿版
bash ~/.agents/skills/academic-paper/scripts/check_hard_rules.sh \
  paper.pdf acl submission --paper-type long

# 示例：NeurIPS camera-ready + 提供 LaTeX 日志
bash ~/.agents/skills/academic-paper/scripts/check_hard_rules.sh \
  paper.pdf neurips camera-ready --log main.log

# 完整参数
#   --paper-type <long|short>   ACL/EMNLP 用（默认 long）
#   --log <path>                提供 LaTeX .log，额外检查编译错误
#   --no-blind                  跳过匿名性检查（非双盲会议）
```

脚本覆盖的硬规则详见下方「硬规则清单」。

---

## 硬规则清单

以下规则由脚本自动检测，结果为 ✅ PASS / ⚠️ WARN / ❌ FAIL：

### 通用（所有会议/类型）

| # | 规则 | 检测方式 |
|---|------|---------|
| H1 | 纸张尺寸 = US Letter (612 × 792 pts) | `pdfinfo` Page size |
| H2 | 无 `[?]` 未解析引用 | `pdftotext` + grep `\[?\]` |
| H3 | PDF 文件 < 50 MB | `stat` 文件大小 |

### Camera-ready 专属

| # | 规则 | 检测方式 |
|---|------|---------|
| H4 | 所有字体已嵌入 | `pdffonts` emb 列全为 yes |
| H5 | PDF 元数据无作者字段（如已清除 Author 字段则 ✅） | `pdfinfo` Author |

### 双盲投稿版专属

| # | 规则 | 检测方式 |
|---|------|---------|
| H6 | PDF 元数据无作者字段 | `pdfinfo` Author |
| H7 | 正文无"our previous/prior/earlier work" | `pdftotext` + grep |
| H8 | 正文无机构名（university / institute / laboratory） | `pdftotext` + grep |
| H9 | 正文无致谢资助信息（funded by / grant / support from） | `pdftotext` + grep |
| H10 | 正文无可追踪链接（http/https URL） | `pdftotext` + grep |

### 会议专属必需章节

| # | 规则 | 适用会议 | 检测方式 |
|---|------|---------|---------|
| H11 | 含 "Limitations" 章节 | ACL / EMNLP（缺失 = desk reject） | `pdftotext` + grep |
| H12 | 含 "Responsible NLP" / "Ethics" checklist | ACL / EMNLP（缺失可能 desk reject） | `pdftotext` + grep |
| H13 | 含 "Broader Impact" / "Impact Statement" | ICML（强烈推荐） | `pdftotext` + grep |

### LaTeX 日志（提供 --log 时）

| # | 规则 | 检测方式 |
|---|------|---------|
| H14 | 无致命编译错误（`!` 行） | grep `^!` |
| H15 | 无未定义引用（`Citation ... undefined`） | grep |
| H16 | 无重复 label（`multiply defined`） | grep |
| H17 | Overfull \hbox 数量 | grep 并统计 |

> **页数说明**：PDF 总页数由脚本报告，但**不做 FAIL 判定**——因为脚本无法区分正文页与参考文献/附录页。用户需对照会议规则手动确认。AAAI 的参考文献计入正文页数，请特别注意。

---

## 视觉审查（可选）

用户明确要求时（如"帮我看看视觉效果"）才执行。将 PDF 转为页面图片，逐页调用 pi-subagent 的 figure-qa agent（调用方式详见 `~/.agents/skills/pi-subagent/agents/figure-qa.md`）：

```bash
mkdir -p /tmp/paper-review
pdftoppm -jpeg -jpegopt quality=85 -r 150 paper.pdf /tmp/paper-review/page
```

> 150 DPI JPEG q85：每页约 50KB，双栏小字仍可读，figure-qa 内部会进一步压缩。

为每页调用 figure-qa（scene: `academic`）：

```bash
bash ~/.agents/skills/pi-subagent/scripts/invoke.sh \
  --agent figure-qa \
  --msg "Check the image at: /tmp/paper-review/page-01.jpg\nScene: academic\nIntent: Page N of a <conference> <submission|camera-ready> paper\nCheck for: margin overflow, figure/table readability, label overlap, caption placement (figure=below table=above), column alignment, font size consistency, grayscale distinguishability, author visibility"
```

figure-qa 自动覆盖的检查项：

| 检查项 | 具体内容 |
|--------|---------|
| 边距 | 内容是否侵入页边距 |
| 图表可读性 | 图中文字可辨识、label 无重叠 |
| Caption 位置 | 图的 caption 在下方，表的 caption 在上方 |
| 双栏对齐 | 两栏底部大致齐平 |
| 字号一致性 | 正文、图注、脚注字号是否符合模板 |
| 色彩可辨识 | 灰度下仍可区分 |
| 首页信息 | 投稿版无作者；camera-ready 有完整作者信息 |

---

## 输出报告模板

```markdown
# 格式检查报告

**会议**: [name]  **类型**: [submission/camera-ready]  **日期**: [date]

## 硬规则结果（自动化）

| # | 规则 | 状态 | 说明 |
|---|------|------|------|
| H1 | 纸张尺寸 | ✅ | 612 × 792 pts (US Letter) |
| H2 | 未解析引用 | ✅ | 0 个 [?] |
| H3 | 文件大小 | ✅ | 3.2 MB |
| H4 | 字体嵌入 | ❌ | 2 个字体未嵌入: ... |
| ... | | | |

**页数**: X 页（总计，含参考文献/附录）— 请手动对照会议页数规则

## 视觉审查结果
（未启用 / 见下方逐页报告）

## ❌ 必须修复（desk reject 风险）
## ⚠️ 建议修复
## ✅ 已通过
```

---

## 重要提醒

- 规则每年可能变化，始终以当年官网 CFP 为准
- **ACL/ARR Limitations 缺失 = desk reject**
- **AAAI 参考文献计入页数**（唯一例外）
- **ICLR 有 6 页下限**（2025 新增）
- 双盲匿名：允许公开 arXiv 预印本，但投稿版正文不能含作者信息
