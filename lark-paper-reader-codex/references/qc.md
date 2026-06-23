# Quality Check (QC) Gate For Lark Paper Reader Codex

QC 指 Quality Check / 质量检查。交付前必须做结构检查；有问题就修复并重跑。视觉检查尽力完成，不能完成时要在最终回复说明。

## Required Checks

1. 没有重复图片。
2. 没有重复评论。
3. 没有 `[图X位置...]` 占位符残留。
4. 没有裸 XML：`&lt;text&gt;`、`&lt;equation`、`</equation>` 字面文本。
5. 没有明显未渲染公式：正文或 callout 中残留 `$...$`、`$$...$$`。
6. 导读、作者思考路径、图表读法、公式解释、具象化、疑问、引用背景至少按论文内容合理覆盖。
7. 摘要、引言、方法、实验、结论和附录没有被意外丢失；若原论文没有对应章节，记录原因。
8. 正文仍是按原论文结构逐段翻译，不得用总结、导读、解读或讲义替代原文翻译。
9. 注释内容中的额外解释必须是 XML callout，不得以 Markdown `>` blockquote 残留在正文。
10. comment 必须是局部边注；若使用全文评论，必须记录定位失败原因。常规中长论文少于 8 条 comment 视为风险。
11. 正式文档不得包含执行过程、工具限制、权限判断、代理使用状态或 checkpoint/QC 说明；这些信息只能存在于内部文件和最终交付说明。
12. 正式方法章节前必须有作者思考路径 callout；核心图表后必须有图表读法 callout。若缺失，必须在 `qc-report.md` 写明论文结构原因或定位失败原因。
13. 风格必须对齐 `references/style-standard.md`，尤其是 outline、导读、图表读法、公式直觉、术语表和最终汇报口径。

## XML Fetch

```bash
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user > "$WORK_DIR/lark-full.xml.json"
```

用 Python 读取 `data.document.content`，检查：

- `re.findall(r'<img[^>]+>', content)`
- `Counter` 统计图片 `name` 或 `src`
- `re.findall(r'\[图\d+位置[^\]]*\]', content)`
- `'$' in content`
- `'&lt;text' in content` 或 `'&lt;equation' in content`
- `emoji="..."` 统计 callout 覆盖
- 作者思考路径可用 `作者可能的思考路径`、`阅读辅助推断` 或 `🧭` 检查。
- 图表读法可用 `图表读法`、`这张图在论文里负责什么` 或 `📊` 检查。
- 抽样检查每个主章节前 2-3 个正文段落，确认它们对应原文段落翻译，而不是“本节主要说明...”式总结或讲义。
- 对照 `references/style-standard.md` 检查 outline、callout 类型和术语表结构。

正式文档卫生检查还必须搜索下列元说明；若命中不是论文原文、题名、引用或代码仓库内容，必须删除后重新 fetch/export：

- `本文档采用`
- `Mode`
- `未启用子代理`
- `未启用多代理`
- `Codex 本体`
- `工具规则`
- `权限判断`
- `translation-plan.md`
- `annotations.json`
- `qc-report.md`
- `lark-cli`

## Comments

```bash
lark-cli drive file.comments list \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"is_whole\":false,\"page_size\":100}" \
  --as user > "$WORK_DIR/lark-comments.json"
```

提取每条 reply 的 `text_run.text`，按前 80 个字符统计重复。重复评论一般保留一个，其余设为 solved：

```bash
lark-cli drive file.comments patch \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"comment_id\":\"$COMMENT_ID\"}" \
  --data '{"is_solved":true}' \
  --as user
```

如果 `is_whole=false` 返回 0 条，再查 `is_whole=true`。全文评论不计入“边注覆盖率”，只能作为降级记录。

## Export And Visual Check

导出 PDF：

```bash
cd "$WORK_DIR"
lark-cli drive +export \
  --token "$DOC" \
  --doc-type docx \
  --file-extension pdf \
  --output-dir . \
  --overwrite \
  --as user
```

转 PNG：

```bash
mkdir -p "$WORK_DIR/pages"
pdftoppm -r 150 -png "$WORK_DIR/output.pdf" "$WORK_DIR/pages/page"
```

视觉检查重点：

- 公式是否显示为公式，而不是 LaTeX 字符串或红色错误。
- 图片是否显示、顺序是否正确、caption 是否对应。
- callout 是否渲染为彩色块，内部代码块没有逃逸。
- 是否出现 XML 标签、乱码、重复大段文本。
- 标题层级和段落间距是否可读。

## Final Report Template

```markdown
# QC Report

- Document: <doc title/link>
- Images: <count>, duplicates: <none/list>
- Comments: <count>, duplicates: <none/list>
- Placeholders: <none/list>
- Formula issues: <none/list>
- Bare XML: <none/list>
- Translation body: <pass/issues>
- Public document hygiene: <pass/issues>
- Style standard: <pass/issues>
- Callouts: 📍 <n>, 🧭 <n>, 📊 <n>, 💡 <n>, 🌉 <n>, ❓ <n>, 📖 <n>, 🔧 <n>
- Local comments: <count>, full comments: <count>, duplicates: <none/list>
- PDF export: <done/failed>
- Visual check: <done/partial/not available>
- Remaining risks: <none/list>
```
