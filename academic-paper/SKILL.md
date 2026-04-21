---
name: academic-paper
description: >
  AI 学术论文全周期写作。覆盖获取模板、Overleaf 项目创建、结构化写作、配图生成、
  格式检查、投稿前审查。内置论文配图（figure-gen）与格式检查（format-check）子模块。
  搭配 overleaf、gemini-image-gen、visual-checker、ph-paper-helper 使用。
  触发语境："写论文""paper writing""投稿前检查""画个架构图""论文配图""格式检查""desk reject"。
---

# Academic Paper

AI 学术论文全周期写作 skill。从获取模板到投稿终审。

## 搭配 Skills

| Skill | 用途 | 何时调用 |
|-------|------|---------|
| **overleaf** | 创建项目 / git clone-push / 编译 / 下载 PDF / review 评论 | 项目初始化及全程同步 |
| **gemini-image-gen** | Gemini 图片生成引擎（text-to-image / image-to-image / 多分辨率） | 配图子模块的底层引擎 |
| **visual-checker** | 视觉 QA 子代理（academic / slides / general scene） | 配图审查、格式视觉审查 |
| **ph-paper-helper** | 论文检索 / 导入 / BibTeX 导出与补全（`ph add --bib` / `ph enrich`） | 文献引用处理 |

---

## 准备阶段

### 1. 确认目标会议与模板

在写任何内容之前，必须确认：

1. **目标会议 + 年份**（如 NeurIPS 2025、ACL 2025）
2. **论文类型**（long / short / workshop / position）
3. **页数限制**（见下方速查表）
4. **DDL**

然后去**该会议官网**下载当年官方 LaTeX 模板。不同年份模板不同，不可复用旧版。

> ⚠️ 不要猜模板链接。每年 CFP 页面会更新模板下载地址。直接搜索 `<Conference> <Year> call for papers` 获取最新版。

### 页数速查

| 会议 | 投稿正文 | Camera-ready | 参考文献 | 备注 |
|------|---------|-------------|---------|------|
| NeurIPS | 10 页 | 10 页 | 不计 | 含图表，不含参考文献/附录 |
| ICML | 8 页 | 9 页 | 不计 | 不含参考文献/Impact/附录 |
| ICLR | 6-10 页 | 同投稿 | 不计 | 6 页下限（2025 新增）|
| ACL/ARR Long | 8 页 | 9 页 | 不计 | Limitations **必须有** |
| ACL/ARR Short | 4 页 | 5 页 | 不计 | 同上 |
| AAAI | 7 页 + 2 附加 | 同投稿 | **计入** | 唯一参考文献计入页数 |

会议格式详表见 [references/conference-rules.md](references/conference-rules.md)。

### 2. 创建 Overleaf 项目

确认论文项目名后，通过 overleaf skill 创建项目、克隆到本地：

```
1. overleaf: 创建项目 "<论文名>"
2. 克隆到本地工作目录
3. 将下载的官方模板文件放入项目
4. push 到 Overleaf 确认编译通过
```

### 3. 检查参考文献

检查项目中是否已有 `.bib` 文件：

- **已有 `.bib`** → 使用 ph-paper-helper 的 `ph enrich --bib <file>.bib` 补全不完整的元数据
- **没有 `.bib`** → 创建空 `references.bib`，在全部写作完成后提醒用户补充参考文献。写作过程中遇到需要引用的地方先用 `\cite{TODO-xxx}` 占位

---

## 写作阶段

本 skill 不限定写作顺序、字数分配或段落结构。论文内容由用户主导，agent 辅助执行。

LaTeX 相关资源分三类，不同阶段使用：

| 类别 | 文件 | 何时使用 |
|------|------|----------|
| **写前注入** | [references/latex-writing-prefs.md](references/latex-writing-prefs.md) | 开始写作前读取，轻量偏好提醒 |
| **写完后 lint** | `scripts/latex_lint.py`、`scripts/check_hard_rules.sh` | 源码/PDF 硬规则自动检查 |
| **写完后 review** | [references/latex-review-checklist.md](references/latex-review-checklist.md) | 人工复查，向用户汇报 |

完整规范参考：[references/latex-norms.md](references/latex-norms.md)（含 [AUTO]/[MANUAL] 标注）。

```bash
# Linter
python3 ~/.agents/skills/academic-paper/scripts/latex_lint.py <file> [--bib] [--fix-preview] [--severity WARN]

# PDF 硬规则
bash ~/.agents/skills/academic-paper/scripts/check_hard_rules.sh paper.pdf <conf> <submission|camera-ready>
```

---

## 配图生成

详见 [references/figure-gen.md](references/figure-gen.md)。

底层引擎：gemini-image-gen；视觉审查：visual-checker（scene: `academic`）；最多 3 轮 inspect-revise，确认后升 4K 终稿。

> 数据驱动图表（bar chart / line plot / heatmap）用 matplotlib/seaborn 直接绘制，不走本模块。

<!-- figure-gen content moved to references/figure-gen.md -->

## 格式检查

详见 [references/format-check.md](references/format-check.md)。

硬规则自动检查脚本（纸张尺寸 / 字体嵌入 / 匿名性 / 必需章节 / 编译日志等）：

```bash
bash ~/.agents/skills/academic-paper/scripts/check_hard_rules.sh \
  paper.pdf <conference> <submission|camera-ready> [--paper-type long|short] [--log main.log]
```

脚本失败（exit 1）= 存在 desk-reject 风险的硬规则违反；警告（exit 0）= 需人工复核。
视觉审查（逐页 visual-checker）默认关闭，用户明确要求时启用。

<!-- format-check content moved to references/format-check.md -->

## 投稿前自查清单

- [ ] 所有 `\cite{TODO-xxx}` 占位已替换为真实引用
- [ ] Abstract 与 Introduction 末尾的贡献点一致
- [ ] 每个 Figure / Table 在正文中被 `\ref` 引用
- [ ] 每个编号公式在正文中被 `\eqref` 引用
- [ ] 缩写首次出现时展开
- [ ] 数字精度统一（如都保留两位小数）
- [ ] 参考文献无重复条目、格式统一
- [ ] `.bib` 中所有条目元数据完整（用 `ph enrich --bib` 检查）
- [ ] 没有 `[?]` 未解析引用
- [ ] 没有 `Overfull \hbox` 超过 1pt 的警告
- [ ] Camera-ready：作者信息完整、去掉行号、补充 Acknowledgements
- [ ] 投稿版：无作者信息、有行号
- [ ] ACL/ARR：Limitations 章节存在、Responsible NLP Checklist 已填
- [ ] PDF < 50MB
- [ ] 匿名 code repo（如 anonymous.4open.science）已准备（如需要）

---

## 重要提醒

- **不同年份规则可能变化** — 始终去官网确认当年 CFP
- **ACL/ARR 的 Limitations 章节缺失 = desk reject**
- **AAAI 参考文献计入页数**（唯一例外）
- **ICLR 2025 新增 6 页下限**
- 页数计算方式各会不同，务必按目标会议规则判断
