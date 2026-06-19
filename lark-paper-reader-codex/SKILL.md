---
name: lark-paper-reader-codex
description: Codex 专用：将学术论文整理为飞书原文翻译或注释文档。触发语境：帮我原文翻译/逐段翻译这篇论文、上传到飞书、arxiv://xxx 注释、给 paper 做 Codex 版飞书笔记。
metadata:
  requires:
    bins: ["lark-cli"]
    skills: ["lark", "ph-paper-helper"]
---

# lark-paper-reader-codex

把一篇论文整理成可直接阅读的飞书原文翻译或注释文档。默认优先输出逐段忠实翻译：中文正文、原图、公式、术语表，严格保留章节层级与论证顺序；导读 callout、关键参考文献和代码映射只在用户明确要求时补充。这个版本面向 Codex 执行，不使用 Pi、Herdr pane 或固定模型子代理；但在 Annotated Reader Mode 下，必须先检查 Codex 当前是否有可用的子代理/并行工作者能力。若工具可用且工具规则要求用户显式授权，必须先向用户请求授权；只有在用户未授权、拒绝授权或当前环境确无可调用子代理工具时，才降级为 Codex 本体分批处理，并且降级记录只写入内部 checkpoint/QC，不写入正式文档。

## When To Use

用户给出 arXiv ID、arXiv URL、DOI、论文 PDF 或让你“读论文并上传到飞书”时使用。若用户只想要本地总结、BibTeX、论文检索或不需要飞书文档，优先使用 `ph-paper-helper` 或普通回答。

## Codex Principles

- 使用当前工作区下的 `work/lark-paper-reader/<paper-id>/` 保存中间文件；只把最终可交付产物放入 `outputs/`。
- 需要读取配套细节时再打开 references：飞书 XML 与公式规则见 `references/lark-doc-rules.md`，注释层规则见 `references/annotate.md`，质量检查见 `references/qc.md`。
- 不调用 `pi --print`、Herdr pane 或 Pi 专用模型。Annotated Reader Mode 下必须优先发现 Codex 当前可用的子代理/多代理工具来生成段落摘要、术语边注候选和视觉审查；若发现到的工具规则要求用户显式授权且用户尚未授权，必须暂停论文生成并用一句话请求授权。不得把“用户未授权”当作既成事实静默降级。
- 若用户拒绝授权、未在本轮授权，或当前环境确无可调用子代理工具，必须在 `annotations.json` 与 `qc-report.md` 说明“未启用子代理，已由 Codex 本体分批完成”及具体原因；不得把该说明写入正式 Markdown、飞书正文、callout、边注或导出的 PDF。
- 每一步都留下可恢复的 checkpoint：`metadata.json`、`glossary.md`、`translated.md`、`figures.json`、`annotations.json`、`qc-report.md`。
- 若发现已有同一论文的飞书文档，先向用户展示已有链接并暂停，除非用户明确要求重新创建。

## Public Document Hygiene

正式读者文档只承载论文内容和面向读者的注释层。`translated.md`、传给飞书的 Markdown/XML、飞书正文、callout、comment 和导出的 PDF/Markdown 中，严禁出现执行过程、工具限制、权限判断、代理使用状态或 checkpoint/QC 说明，例如：

- “本文档采用 Annotated Reader Mode / Strict Translation Mode”
- “未启用子代理 / 未启用多代理 / Codex 本体分批完成”
- “当前工具规则要求用户显式授权”
- `translation-plan.md`、`annotations.json`、`qc-report.md`、`lark-cli` 等内部产物或命令说明

这些信息只能出现在内部 checkpoint/QC 文件和最终给用户的交付说明中。若某个禁用词本身是论文原文、题名、引用或代码仓库内容，允许保留，但必须在 `qc-report.md` 标注为论文内容命中。

## Translation Contract

- 用户只要说“翻译 / 原文翻译 / 逐段翻译 / 忠实翻译”，默认进入 **Strict Translation Mode**。
- Strict Translation Mode 下，`translated.md` 必须以原文结构为准：按章节、段落、列表、图注、表注、附录原序翻译，不主动改写、不主动总结、不主动补背景。
- 严禁默认加入导读 callout、阅读路线、问题清单、长篇解释、实现映射或额外评论。
- 术语可以统一译名，但不要把术语表内容扩写进正文；正文只负责翻译原文，不负责讲解原文。
- 只有当用户明确要求“注释 / 导读 / 背景 / 代码映射 / 阅读提示”时，才在翻译之外追加阅读层。

## Mode Resolution

执行前必须在 `translation-plan.md` 中写明模式，且最终回复也要报告模式：

- **Strict Translation Mode**：触发词包括“原文翻译”“逐段翻译”“忠实翻译”“翻译全文”“只翻译”。目标是翻译，不是解读。
- **Annotated Reader Mode**：触发词包括“读论文”“精读”“注释版”“导读”“帮我理解”“加背景”“代码映射”。目标是像高质量论文笔记一样帮助阅读。
- 如果用户同时说“原文翻译”和“注释/导读”，先以原文翻译为正文主产物；注释层只能放在独立的“译者注/阅读层”区域，不能改写或替代正文。
- 如果用户只给 URL 和 skill 名但没有说明模式，默认 **Annotated Reader Mode**；但若上下文中用户曾强调“原文翻译”，延续 Strict Translation Mode。

## Quality Bars

### Strict Translation Mode

- 主文正文必须逐段覆盖：摘要、引言、预备知识/背景、方法、实验、相关工作、结论。
- 原文中的图、表、算法、公式、脚注、图注、表注必须保留；大型表格可在飞书中用表格或等价 Markdown 表达，不能只写“见表”。
- 附录默认覆盖到同等层级；若因篇幅只翻译附录要点，必须在 `qc-report.md` 和最终回复中明确标为“非完整附录翻译”。
- 不得把“作者提出/本文答案/阅读路线/常见疑问/公式直觉/实现要点”等导读语气混入正文。
- QC 必须检查：导读词残留、表格/算法遗漏、占位符残留、裸 XML、字面公式残留、关键章节遗漏。

### Annotated Reader Mode

以既有高质量文档《MR-Search：基于自我反思的元强化学习智能搜索》为质量标尺，至少包含：

- 元信息与作者/机构/代码链接。
- 导读 callout：核心问题、本文答案、预备知识速查、阅读路径建议。
- 正文中文翻译或忠实转述，保留原论文章节顺序。
- 图、表、公式、算法原位插入，并补充中文图注/表注。
- 公式直觉 callout：解释关键公式为什么这样设计、解决什么问题。
- 方法具象化 callout：把抽象机制映射到一个可理解例子。
- 关键引用背景：展开 3 到 5 篇对理解论文最重要的一跳引用。
- 若有代码仓库，做代码映射：仓库结构、关键文件、论文模块到实现位置、必要代码片段。
- 实验读法：主结果、消融、扩展实验、局限和失败案例。
- 附录覆盖：实验细节、额外结果、案例研究、局限，不要只停在主文。

## Input Normalization

接受：

- `2604.14010`
- `arxiv://2604.14010`
- `https://arxiv.org/abs/2604.14010`
- `https://arxiv.org/pdf/2604.14010`
- `doi://10.48550/arXiv.2604.14010`

统一转成 `ph` 可接受的 URI，例如 `arxiv://2604.14010` 或 `doi://...`。为文件路径生成安全 ID 时，将 `/`、`:`、`.` 等替换成 `_`。

## Workflow

1. **Preflight**
   - 运行 `lark-cli auth status` 确认飞书登录。
   - 运行 `uv run --project "$HOME/project/ph2" ph --version` 确认 `ph` 可用。
   - 建立工作目录：`work/lark-paper-reader/<safe-paper-id>/`。

2. **Duplicate Check**
   - 用论文 ID 搜索飞书：`lark-cli docs +search --query "$ARXIV_ID" --as user`。
   - 搜索结果在 `data.results` 中，不是 `items`。
   - 若标题或摘要命中同一 ID，向用户展示文档标题和 URL，并停止等待确认。

3. **Fetch Paper Source**
   - `ph import --input <paper-uri>` 只用于入库和元信息补全。
   - 对 arXiv 论文，默认下载 arXiv PDF 与 e-print LaTeX source：`https://arxiv.org/pdf/<id>` 与 `https://arxiv.org/e-print/<id>`。
   - 解包 source，优先从 `.tex`、`.bbl/.bib`、`figures/`、`00README.json` 构建正文、图片、公式、表格和引用清单；原始 PDF 只用于核对分页/文本和视觉导出。
   - 只有当 arXiv source 不可用、不是 LaTeX、缺关键图片/表格，或用户提供的是非 arXiv PDF/DOI 时，才 fallback 到 MinerU：`ph fetch --paper-id <paper-uri> --force --include-content`。
   - fallback 到 MinerU 时，从返回的 `full_text_path` 推导 `PAPER_DIR`，不要手拼 ph 缓存路径；并在 `metadata.json`、`translation-plan.md`、`qc-report.md` 记录触发原因。

4. **Plan The Document**
   - arXiv source 路径：从主 `.tex` 提取标题、作者、年份、摘要、章节、图片引用、公式、表格、算法、参考文献和 GitHub URL；从 PDF 文本抽取核对章节顺序。
   - MinerU fallback 路径：从 `full.md` 提取标题、作者、年份、摘要、章节、图片引用、公式、参考文献和 GitHub URL。
   - 写 `metadata.json`、`figures.json` 和 `translation-plan.md`。
   - 在 `translation-plan.md` 首行写明 `Mode: Strict Translation` 或 `Mode: Annotated Reader`，并列出包含/排除项。
   - 建立 `glossary.md`：A 类使用中文共识译名，B 类首次出现写“中文（英文全称，缩写）”，C 类保留英文。
   - Annotated Reader Mode 还必须写 `annotation-plan.json`：列出待加 callout 的公式/方法步骤/引用/疑问，以及待加 comment 的术语和高语义载荷段落。该清单处理完一个标记一个，不得凭感觉少量添加。

5. **Translate**
   - 写 `translated.md`，默认执行逐段忠实翻译：保留章节层级、段落顺序、公式 LaTeX、表格、图表占位和附录。
   - 不要主动改写成总结、导读、解读或评论。
   - 独立公式保留 `$$...$$`，行内公式保留 `$...$`；不要转成 Unicode 数学符号。
   - 在图所在位置写稳定占位符，如 `[图1位置: <image-file>]`，后续插图后删除。
   - 长文分批写入文件，但不要依赖某个特定 agent 的 `write` 工具说明。

6. **Create Lark Doc**
   - 用 `lark-cli docs +create --api-version v2 --doc-format markdown --content @translated.md --parent-position my_library --as user` 创建文档。
   - 创建后用 `drive files patch` 修复内部标题和 Drive 文件名。
   - 在标题后插入论文元信息 callout：标题、作者、年份、arXiv/DOI、PDF 链接、创建时间。
   - 如果是 Strict Translation Mode，元信息之外不要自动加导读 callout。
   - Fetch XML 验证公式实际状态；如果公式仍是字面 `$...$` 或 `$$...$$`，按 `references/lark-doc-rules.md` 修复。

7. **Insert Figures**
   - 只插入正文实际引用的图片；arXiv source 路径以 `.tex` 的 `\includegraphics` 顺序为准，MinerU fallback 路径以 `full.md` 引用顺序为准。
   - 对 PDF/EPS/SVG 图先本地转换为 PNG，写入工作区 `images/`，再插入飞书。
   - `lark-cli docs +media-insert --file` 要求从图片目录执行，传相对文件名。
   - 用图片前后唯一中文文本定位；若歧义，改用更长的 `start...end` anchor。
   - 插入完成后 fetch XML 删除所有 `[图X位置...]` 占位符块。

8. **Add Reading Layer**
   - 仅在 Annotated Reader Mode，或用户明确要求注释版/导读版时执行。
   - 必须先读取 `references/annotate.md` 并执行其中的 5-PRE 扫描：fetch 文档 XML/with-ids，列出公式、方法步骤、重要引用、长段落、术语首次出现，写入 `annotation-plan.json`。
   - 额外解释（导读、公式直觉、具象化、引用背景、实现要点、读者疑问）必须作为飞书原生 XML `<callout>` 块插入到对应 block 后，不能写成正文 Markdown blockquote，也不能把解释混入翻译正文。
   - 边注必须用飞书 comment，锚定到具体术语或具体段落；优先 `--selection-with-ellipsis` 唯一定位，歧义时 fetch with-ids 后用 `--block-id`，不得用全文评论冒充边注。
   - Annotated Reader Mode 必须有足量边注：至少覆盖所有核心术语首次出现，并覆盖语义载荷高的关键段落；少于 8 条 comment 时必须在 `qc-report.md` 说明论文很短或定位失败原因。
   - 若论文有 GitHub 仓库，浅克隆到工作目录，先写架构地图，再把关键实现片段以内嵌代码块加入 `🔧` callout。

9. **References**
   - 只展开 3 到 5 篇高价值 1-hop 引用：理论基础、主要 baseline、被反复比较的工作。
   - 用 `ph search` 或 `ph fetch` 获取元信息和必要摘要，不要为了装饰性引用拉太多论文。

10. **QC And Visual Gate**
    - 按 `references/qc.md` 跑结构检查：重复图片、重复评论、占位符残留、裸 XML、公式字面残留、关键章节缺失。
    - Strict Translation Mode 额外检查：导读/常见疑问/实现要点/阅读路径等注释层词汇不得出现在正文；表格、算法、附录覆盖状态必须记录。
    - Annotated Reader Mode 额外检查：是否包含导读、公式直觉、引用背景、实验读法、局限、代码映射（若有仓库）和附录覆盖。
    - 正式文档卫生检查：fetch/export 后搜索“本文档采用 Annotated Reader Mode”“未启用子代理”“未启用多代理”“Codex 本体”“工具规则”“用户显式授权”“translation-plan.md”“annotations.json”“qc-report.md”“lark-cli”等元说明；若命中不是论文内容，必须删除后重新导出检查。
    - 导出 PDF 并转 PNG。若当前 Codex 环境有视觉查看能力，抽样或逐页检查公式、图片、callout 和排版；否则保留 PNG/PDF 路径并说明未做视觉模型审查。
    - 修复问题后重新跑 QC，最终给用户飞书链接、PDF/PNG 检查结果和残余风险。

## Lark Command Notes

- `--api-version v2` 只用于 `docs +create` 的 Markdown 建文档。fetch、update、block 操作使用默认版本。
- `docs +create --title` 可能只设置 Drive 文件名；创建后用 `drive files patch` 设置最终标题。
- `block_replace` 写 XML 时不要在 `<p>` 里包 `<text>` 子元素；对行内公式使用 `<latex>...</latex>`。
- callout 里的公式必须写成 `<latex>...</latex>`，不要写 Markdown `$...$`。
- 多行代码块用 `<pre lang="python"><code>...</code></pre>`，可以放在 `<callout>` 内。

## Deliverable

最终回复包含：

- 飞书文档标题和链接。
- 是否为 Strict Translation Mode 以及是否额外添加注释层。
- 是否发现重复文档，以及用户是否要求重建。
- 图片数量、评论数量、callout 覆盖简报。
- QC 结果和是否完成 PDF/PNG 视觉检查。
- 如果某一步因权限、导出或工具缺失失败，明确说明失败点和可恢复的本地 checkpoint。
