---
name: hjfy-pdf-to-lark
description: 从 hjfy.top 论文页或 arXiv ID 获取中文翻译 PDF，并上传到用户自己的飞书云空间或知识库节点。用于“把幻觉翻译 PDF 导入飞书”“上传 hjfy 译文到飞书”“保存 arXiv 中文 PDF 到 Lark/Feishu”等请求；只研究方法时保持只读，明确要求导入时执行下载与上传。
---

# HJFY PDF To Lark

把幻觉翻译生成的中文 PDF 作为普通文件上传到飞书 Drive。PDF 不能通过
`drive +import` 转成飞书在线文档；应使用 `drive +upload`。

## 依赖与前置阅读

1. 解析网页或下载前，遵循 `web-reader` 的网页读取与动态页面兜底规则。
2. 调用飞书前，完整阅读同级 `lark/SKILL.md` 的共享认证规则和
   `lark/references/drive/lark-drive-upload.md`。
3. 确认 `curl`、`jq` 和 `lark-cli` 可用。
4. 用 `lark-cli auth status --json` 确认 user 身份可用且含
   `drive:file:upload`。`needs_refresh` 可由下一次 user API 调用自动刷新。

## 意图分流

- 用户只问“怎么做”“研究一下”时，保持只读：说明接口、下载和上传命令，
  最多执行 `lark-cli drive +upload --dry-run`，不要真的上传。
- 用户明确要求“导入”“上传”“保存到我的飞书”时，视为已授权该次上传。
  下载完成并验证后，以 user 身份执行上传。
- 用户没有指定目标位置时，上传到其 Drive 根目录；不要为了根目录传空 token。
- 用户给出文件夹 token 时用 `--folder-token`；给出 Wiki node token 时用
  `--wiki-token`。两者互斥。不要把 `space_id` 当作 Wiki node token。

## 工作流

### 1. 下载中文 PDF

解析 `scripts/download_hjfy_pdf.sh` 相对于本 `SKILL.md` 的绝对路径，再执行：

```bash
tmp_dir="$(mktemp -d)"
download_json="$(/absolute/path/to/scripts/download_hjfy_pdf.sh \
  --input 'https://hjfy.top/arxiv/2608.10538' \
  --output-dir "$tmp_dir")"
pdf_path="$(printf '%s' "$download_json" | jq -r '.path')"
```

脚本接受 HJFY 页面 URL、arXiv URL、现代 arXiv ID，以及旧式
`subject/number` ID。它会：

1. 查询 `https://hjfy.top/api/arxivStatus/{id}`，只在状态为 `finished` 时继续。
2. 查询 `https://hjfy.top/api/arxivFiles/{id}`，读取 `data.zhCN`。
3. 立即下载短时有效的签名 URL。
4. 检查 `%PDF-` 文件头，原子写入目标文件，并仅输出不含签名 URL 的 JSON。

不要缓存、展示或记录 `data.zhCN` 的完整签名 URL。链接通常几分钟后失效；
下载失败且疑似过期时，重新获取 `arxivFiles` 响应，而不是重用旧 URL。

### 2. 选择上传名称

默认使用 `<arxiv-id>_zh_CN.pdf`。如果论文标题清晰，可使用
`<简短标题>-中文翻译-<arxiv-id>.pdf`，同时去掉 `/`、控制字符等不安全字符。
不要改变 `.pdf` 扩展名。

### 3. 上传到用户自己的飞书

始终显式使用 `--as user`：

```bash
lark-cli drive +upload \
  --as user \
  --file "$pdf_path" \
  --name '<上传后的文件名>.pdf' \
  --json
```

按需增加且只增加一个目标参数：

```bash
--folder-token '<folder_token>'
--wiki-token '<wiki_node_token>'
```

`drive +upload` 会自动对超过 20 MB 的文件使用分片上传，并在成功后查询真实
Drive URL。不要改用 bot 身份；“我的飞书”意味着文件应归用户可访问的云空间。

### 4. 验证与汇报

只有同时满足以下条件才报告成功：

1. 下载脚本返回成功，且本地文件已通过 PDF 文件头验证。
2. `lark-cli drive +upload` 返回成功状态和 file token 或真实访问 URL。

输出论文标题、arXiv ID、文件大小、上传位置，以及飞书返回的 URL/token。
不要输出临时签名 URL、access token 或 app secret。

若临时目录由本次任务创建，上传成功后删除；若上传失败，保留 PDF 并报告其
路径，便于重试。不要删除用户原有文件。

## 失败处理

- `status != 0`：报告 HJFY API 的消息，不猜测下载路径。
- 翻译状态不是 `finished`：报告当前状态和论文页 URL；除非用户要求等待，
  不无限轮询。
- `data.zhCN` 缺失：说明当前没有可下载的中文 PDF。
- 下载结果不是 PDF：删除本次产生的无效临时文件并停止上传。
- user 认证或 scope 缺失：按 `lark` skill 的认证流程修复，不静默切到 bot。
- 飞书上传失败：保留已验证的本地 PDF，报告可重试命令和目标位置。
