---
name: lark-paper-reader-codex
description: Codex 专用：将学术论文整理为飞书原文翻译或注释文档。触发语境：帮我原文翻译/逐段翻译这篇论文、上传到飞书、arxiv://xxx 注释、给 paper 做 Codex 版飞书笔记。
metadata:
  requires:
    bins: ["lark-cli"]
    skills: ["lark", "ph-paper-helper"]
---

# lark-paper-reader-codex

把一篇论文整理成可直接阅读的飞书原文翻译或注释文档。默认优先输出逐段忠实翻译：中文正文、原图、公式、术语表，严格保留章节层级与论证顺序；导读 callout、关键参考文献和代码映射只在用户明确要求时补充。这个版本面向 Codex 执行，不使用 Pi、Herdr pane 或固定模型子代理。

## When To Use

用户给出 arXiv ID、arXiv URL、DOI、论文 PDF 或让你“读论文并上传到飞书”时使用。若用户只想要本地总结、BibTeX、论文检索或不需要飞书文档，优先使用 `ph-paper-helper` 或普通回答。

## Codex Principles

- 使用当前工作区下的 `work/lark-paper-reader/<paper-id>/` 保存中间文件；只把最终可交付产物放入 `outputs/`。
- 需要读取配套细节时再打开 references：飞书 XML 与公式规则见 `references/lark-doc-rules.md`，质量检查见 `references/qc.md`。
- 不调用 `pi --print`、Herdr pane、`wait_agent` 或 Pi 专用模型。长段落摘要、视觉检查和代码阅读由 Codex 自己分批完成；可并行的本地读取用 Codex 工具并行。
- 每一步都留下可恢复的 checkpoint：`metadata.json`、`glossary.md`、`translated.md`、`figures.json`、`annotations.json`、`qc-report.md`。
- 若发现已有同一论文的飞书文档，先向用户展示已有链接并暂停，除非用户明确要求重新创建。

## Translation Contract

- 用户只要说“翻译 / 原文翻译 / 逐段翻译 / 忠实翻译”，默认进入 **Strict Translation Mode**。
- Strict Translation Mode 下，`translated.md` 必须以原文结构为准：按章节、段落、列表、图注、表注、附录原序翻译，不主动改写、不主动总结、不主动补背景。
- 严禁默认加入导读 callout、阅读路线、问题清单、长篇解释、实现映射或额外评论。
- 术语可以统一译名，但不要把术语表内容扩写进正文；正文只负责翻译原文，不负责讲解原文。
- 只有当用户明确要求“注释 / 导读 / 背景 / 代码映射 / 阅读提示”时，才在翻译之外追加阅读层。

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

3. **Fetch Paper**
   - `ph import --input <paper-uri>`。
   - `ph fetch --paper-id <paper-uri> --force` 触发 MinerU。
   - 轮询到 `fetch_state=done` 后用 `--include-content` 获取 `full_text_path`。
   - 从 `full_text_path` 推导 `PAPER_DIR`，不要手拼 ph 缓存路径。
   - 检查 `PAPER_DIR/full.md` 和 `PAPER_DIR/images/`；若图片目录为空，重新 `ph fetch --force`。

4. **Plan The Document**
   - 从 `full.md` 提取标题、作者、年份、摘要、章节、图片引用、公式、参考文献和 GitHub URL。
   - 写 `metadata.json`、`figures.json` 和 `translation-plan.md`。
   - 建立 `glossary.md`：A 类使用中文共识译名，B 类首次出现写“中文（英文全称，缩写）”，C 类保留英文。

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
   - 只插入 `full.md` 实际引用的图片，不插 MinerU 产生但正文未引用的裁切图。
   - `lark-cli docs +media-insert --file` 要求从 `PAPER_DIR/images` 执行，传相对文件名。
   - 用图片前后唯一中文文本定位；若歧义，改用更长的 `start...end` anchor。
   - 插入完成后 fetch XML 删除所有 `[图X位置...]` 占位符块。

8. **Add Reading Layer**
   - 仅在用户明确要求注释版或导读版时执行。
   - 插入导读 callout：核心问题、作者答案、阅读路线、预备知识。
   - 在方法和实验部分添加 callout：
     - 公式后加直觉解释。
     - 抽象方法步骤后加具象化示例。
     - baseline 或理论根基首次出现时加引用背景。
     - 算法或开源代码对应处加实现要点。
     - 高密度段落后加读者常见疑问。
   - 添加边注 comment：术语首次出现和特别长的高信息密度段落。
   - 若论文有 GitHub 仓库，浅克隆到工作目录，先写架构地图，再把关键实现片段以内嵌代码块加入 callout。

9. **References**
   - 只展开 3 到 5 篇高价值 1-hop 引用：理论基础、主要 baseline、被反复比较的工作。
   - 用 `ph search` 或 `ph fetch` 获取元信息和必要摘要，不要为了装饰性引用拉太多论文。

10. **QC And Visual Gate**
    - 按 `references/qc.md` 跑结构检查：重复图片、重复评论、占位符残留、裸 XML、公式字面残留、关键章节缺失。
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
