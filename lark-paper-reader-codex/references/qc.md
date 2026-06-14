# QC Gate For Lark Paper Reader Codex

交付前必须做结构检查；有问题就修复并重跑。视觉检查尽力完成，不能完成时要在最终回复说明。

## Required Checks

1. 没有重复图片。
2. 没有重复评论。
3. 没有 `[图X位置...]` 占位符残留。
4. 没有裸 XML：`&lt;text&gt;`、`&lt;equation`、`</equation>` 字面文本。
5. 没有明显未渲染公式：正文或 callout 中残留 `$...$`、`$$...$$`。
6. 导读、公式解释、具象化、疑问、引用背景至少按论文内容合理覆盖。
7. 摘要、引言、方法、实验、结论和附录没有被意外丢失；若原论文没有对应章节，记录原因。

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
- Callouts: 📍 <n>, 💡 <n>, 🌉 <n>, ❓ <n>, 📖 <n>, 🔧 <n>
- PDF export: <done/failed>
- Visual check: <done/partial/not available>
- Remaining risks: <none/list>
```
