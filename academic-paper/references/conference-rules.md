# 会议格式规则详表

基于各会议 2025 年官方 CFP 整理，使用前请确认目标年份是否有更新。

## NeurIPS 2025

- **来源**: https://neurips.cc/Conferences/2025/CallForPapers
- **模板**: `neurips_2025.sty`
- **正文页数**: 10 页（含图表，不含参考文献和附录）
- **Camera-ready**: 10 页正文 + 1 页（共 11 页）
- **参考文献**: 不计入页数，无限制
- **附录**: 不计入页数，审稿人不强制阅读
- **审稿方式**: 双盲
- **纸张**: US Letter (8.5" × 11")
- **必需章节**: Abstract
- **推荐章节**: Broader Impact, Reproducibility Statement
- **匿名要求**: 投稿版不能含作者信息；允许 arXiv 预印本
- **特殊要求**: Ethics review 可能被触发

## ICML 2025

- **来源**: https://icml.cc/Conferences/2025/CallForPapers
- **模板**: `icml2025.sty`（https://media.icml.cc/Conferences/ICML2025/Styles/icml2025.zip）
- **正文页数**: 8 页（不含参考文献、Impact Statement、附录）
- **Camera-ready**: 9 页正文
- **参考文献**: 不计入页数
- **附录**: 不计入页数，与正文在同一文件提交
- **审稿方式**: 双盲
- **纸张**: US Letter
- **必需章节**: Abstract, **Impact Statement**（缺失不会 desk reject 但强烈推荐）
- **匿名要求**: 不能在审稿期间宣传为 ICML 投稿；允许 arXiv
- **特殊要求**: 每位有 4+ 篇投稿的作者必须同意担任审稿人

## ICLR 2025

- **来源**: https://iclr.cc/Conferences/2025/CallForPapers
- **模板**: `iclr2025.sty`（https://github.com/ICLR/Master-Template/raw/master/iclr2025.zip）
- **正文页数**: **6-10 页**（含图表，不含参考文献和附录）；第 11 页出现正文内容 = desk reject
- **页数下限**: 6 页（2025 新增）
- **Camera-ready**: 同投稿限制（6-10 页）
- **参考文献**: 不计入页数
- **附录**: 不计入页数，审稿人不强制阅读
- **审稿方式**: 双盲（OpenReview 公开讨论）
- **纸张**: US Letter
- **匿名要求**: 允许 arXiv；OpenReview 上匿名展示
- **特殊要求**: 投稿后至审稿期间不允许修改论文；讨论阶段允许修改并自动 pdfdiff

## ACL / ARR (ACL Rolling Review)

- **来源**: https://aclrollingreview.org/cfp
- **模板**: ACL 官方 LaTeX 模板（`acl_latex`）
- **Long Paper**: 8 页正文（camera-ready 9 页）
- **Short Paper**: 4 页正文（camera-ready 5 页）
- **参考文献**: 不计入页数，无限制
- **Limitations**: **不计入页数，但必须有**——缺失 = desk reject
- **Ethics/Ethical Considerations**: 推荐，不计入页数
- **Responsible NLP Checklist**: **必须填写**——缺失或不准确可能 desk reject
- **审稿方式**: 双盲（Two-Way Anonymized）
- **纸张**: US Letter
- **匿名要求**: 无匿名期要求（2024 年起）；投稿版必须匿名；补充材料必须匿名；禁止使用可追踪下载的链接（如 Dropbox）
- **适用会议**: ACL, EMNLP, NAACL, EACL 等所有通过 ARR 提交的会议

## EMNLP 2025

- **来源**: https://2025.emnlp.org/calls/main_conference_papers/
- **格式要求**: 完全遵循 ARR 规则（同上）
- **Long Paper**: 8 页 → camera-ready 9 页
- **Short Paper**: 4 页 → camera-ready 5 页
- **审稿方式**: 双盲（通过 ARR）
- **特殊**: 不接受 position paper（2025 主题轨道）

## AAAI 2025

- **来源**: https://aaai.org/conference/aaai/aaai-25/
- **模板**: `aaai25.sty`
- **正文页数**: 7 页（含图表和参考文献）+ 最多 2 页附加内容（ethic statement 等）
- **Camera-ready**: 同投稿
- **参考文献**: **计入页数**（这是 AAAI 独特之处）
- **审稿方式**: 双盲
- **纸张**: US Letter
- **匿名要求**: 标准双盲
- **注意**: 页数含参考文献，这与其他会议不同，容易出错

## 跨会议通用规则

### 字体嵌入
所有会议的 camera-ready 版本都要求字体完全嵌入。检查：
```bash
pdffonts paper.pdf
# 所有字体的 emb 列必须为 "yes"
```

### 纸张尺寸
绝大多数 AI/NLP 会议要求 US Letter (612 × 792 pts)。不是 A4 (595 × 842 pts)。

### 行号
- **投稿版**: 通常需要行号（方便审稿人引用）
- **Camera-ready**: 通常需要去掉行号

### 颜色与可访问性
虽然不是硬性要求，但越来越多的会议建议：
- 图表在灰度下仍可辨识
- 提供高对比度配色
- 不仅依赖颜色传达信息（色盲友好）
