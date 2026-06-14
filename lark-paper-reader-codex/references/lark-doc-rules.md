# Lark Document Rules For Codex

本文件只在实际操作飞书文档时读取。目标是记录稳定的 API 行为和常见坑，避免把大量命令塞进 `SKILL.md`。

## Title

`docs +create --api-version v2 --doc-format markdown --title ...` 可能只设置 Drive 文件名。创建后执行：

```bash
lark-cli drive files patch \
  --params "{\"file_token\":\"$DOC\",\"type\":\"docx\"}" \
  --data "{\"new_title\":\"$PAPER_TITLE\"}" \
  --as user
```

验证：

```bash
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user
```

## Metadata Callout

先 fetch XML，找标题或首个正文块 ID，再插入：

```xml
<callout emoji="📄" background-color="light-gray" border-color="gray">
<p><b>论文标题</b>：...</p>
<p><b>作者</b>：...</p>
<p><b>年份</b>：...</p>
<p><b>原文地址</b>：...</p>
<p><b>论文 PDF</b>：...</p>
<p><b>本文档创建时间</b>：...</p>
</callout>
```

## Formula Policy

创建后必须 fetch XML 看实际状态，再决定是否修复。

合格状态：

- 独立公式是原生公式块，或飞书返回的等价 XML。
- 行内公式在段落内是 `<latex>...</latex>`。
- callout 内公式也是 `<latex>...</latex>`。

需要修复：

- 段落中残留 `$...$` 或 `$$...$$`。
- callout 中残留 `$...$`。
- 出现 `&lt;text&gt;`、`&lt;equation` 等裸 XML。
- `<latex>` 内出现 `&amp;lt;` 或 `&amp;gt;` 双重转义。

XML 写入规则：

```xml
<p>对于每个样本 <latex>x_i</latex>，损失为 <latex>\ell(f(x_i), y_i)</latex>。</p>
```

不要写：

```xml
<p><text>对于每个样本 </text><equation inline="true">x_i</equation></p>
```

## Figure Insertion

`docs +media-insert --file` 只接受相对路径，先进入图片目录：

```bash
cd "$PAPER_DIR/images"
lark-cli docs +media-insert \
  --doc "$DOC" \
  --file "<hash>.jpg" \
  --caption "图1：中文图注" \
  --selection-with-ellipsis "图片前后的唯一文本" \
  --align center \
  --as user
```

定位优先级：

1. 图片前一段的末句。
2. 图片后一段的首句，加 `--before`。
3. 唯一章节标题，加 `--before`。
4. 更长的 `start...end` 省略号 anchor。

插入完成后删除所有 `[图\d+位置.*?]` 占位符块。

## Callout And Code Blocks

可用 callout 类型：

- `📍` 导读指南。
- `💡` 公式直觉和推导。
- `🌉` 抽象方法的具象化例子。
- `📖` 关键引用背景。
- `🔧` 代码实现要点。
- `❓` 读者常见疑问。

代码块放入 callout：

```xml
<callout emoji="🔧" background-color="light-gray" border-color="gray">
<h3>代码：函数名（path/to/file.py）</h3>
<p><b>对应论文：</b>公式(3) / Algorithm 1</p>
<pre lang="python"><code>def step(x):
    return x</code></pre>
<p><b>调用后状态：</b>...</p>
</callout>
```

## Common Fixes

重复图片：fetch XML 找重复 `name` 或 `src`，删除多余 block。

重复 comment：用 `drive file.comments list` 找重复文本，用 `file.comments patch` 将多余评论设为 `is_solved=true`。

`selection-with-ellipsis` 找不到：换更唯一的 anchor，或 fetch `with-ids` 后用 block ID 精确插入附近内容。

`drive +export` 报 unsafe path：进入输出目录后用相对路径导出或下载。
