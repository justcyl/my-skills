# fetch.md — ph + MinerU 获取带图全文

## 完整命令序列

```bash
ARXIV_ID="2604.14010"   # 替换为实际 ID
PH="uv run --project ~/project/ph2 ph"

# Step 1: 导入（自动拉取纯文本，秒级）
$PH import --input arxiv://$ARXIV_ID

# Step 2: 触发 MinerU（异步，通常 1-3 分钟）
$PH fetch --paper-id arxiv://$ARXIV_ID --force

# Step 3: 轮询等待
until $PH fetch --paper-id arxiv://$ARXIV_ID 2>&1 | grep -q '"fetch_state": "done"'; do
    echo "$(date '+%H:%M:%S') MinerU pending..."
    sleep 15
done
echo "✓ MinerU done"

# Step 4: 检查图片是否落地
PAPER_DIR=~/.local/share/ph/papers/arxiv_$(echo $ARXIV_ID | tr '.' '_')
echo "Paper dir: $PAPER_DIR"
ls $PAPER_DIR/
ls $PAPER_DIR/images/ 2>/dev/null | wc -l
```

## 图片落地验证

```bash
IMG_COUNT=$(ls $PAPER_DIR/images/ 2>/dev/null | wc -l)
echo "Images found: $IMG_COUNT"

if [ "$IMG_COUNT" -eq 0 ]; then
    echo "⚠️  images/ 目录为空，重新触发..."
    $PH fetch --paper-id arxiv://$ARXIV_ID --force
    # 再次等待
    until $PH fetch --paper-id arxiv://$ARXIV_ID 2>&1 | grep -q '"fetch_state": "done"'; do
        sleep 15
    done
    IMG_COUNT=$(ls $PAPER_DIR/images/ 2>/dev/null | wc -l)
    echo "Images after retry: $IMG_COUNT"
fi
```

## 解析图片顺序

从 `full.md` 提取图片引用顺序及其对应 caption：

```python
import re

full_md_path = f"{PAPER_DIR}/full.md"
with open(full_md_path) as f:
    content = f.read()

# 找所有图片引用
img_refs = re.findall(r'!\[\]\(images/([a-f0-9]+\.(?:jpg|png))\)', content)

# 找每张图片后紧跟的 Figure caption
figures = []
for i, fname in enumerate(img_refs):
    # 找图片在文中的位置，提取后续的 "Figure X:" 行
    pos = content.find(f"images/{fname}")
    excerpt = content[pos:pos+500]
    fig_match = re.search(r'Figure\s+(\d+)[:\.]?\s*([^\n]+)', excerpt)
    if fig_match:
        fig_num = fig_match.group(1)
        caption_en = fig_match.group(2).strip()
        figures.append((fname, fig_num, caption_en))
    else:
        figures.append((fname, str(i+1), ""))

print(f"Found {len(figures)} figures:")
for fname, num, cap in figures:
    print(f"  fig{num}: {fname} | {cap[:60]}")
```

## 获取全文内容

```bash
# 获取 plain_text（快速，无图，用于翻译参考）
$PH fetch --paper-id arxiv://$ARXIV_ID --include-content \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d['result'][0]
print('plain_text_available:', r.get('plain_text_available'))
print('fetch_state:', r.get('fetch_state'))
print('full_text_path:', r.get('full_text_path'))
"
```

## 注意事项

- `full.md` 里的图片 hash 文件名与 arxiv HTML 的文件名不同，不能直接对应
- 图片数量：MinerU 提取的图片可能多于论文正文中标注的图（含附录图、表格截图等）
- 翻译时用 `full.md` 内容（有正确的图片占位），不要用 Jina/arxiv HTML
- 如果 `PH_MINERU_TOKEN` 未配置，MinerU 不可用，降级为纯文本翻译（无图）
