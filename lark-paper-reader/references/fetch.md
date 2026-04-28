# fetch.md — ph + MinerU 获取带图全文

## 完整命令序列

```bash
ARXIV_ID="2604.14010"   # 替换为实际 ID

# Step 1: 导入（自动拉取纯文本，秒级）
uv run --project "$HOME/project/ph2" ph import --input arxiv://$ARXIV_ID

# Step 2: 触发 MinerU（异步，通常 1-3 分钟）
uv run --project "$HOME/project/ph2" ph fetch --paper-id arxiv://$ARXIV_ID --force

# Step 3: 轮询等待
until uv run --project "$HOME/project/ph2" ph fetch --paper-id arxiv://$ARXIV_ID \
    2>&1 | grep -q '"fetch_state": "done"'; do
    echo "$(date '+%H:%M:%S') MinerU pending..."
    sleep 15
done
echo "✓ MinerU done"

# Step 4: 从 ph 返回的 full_text_path 推导目录（不要自己拼路径）
FULL_MD=$(uv run --project "$HOME/project/ph2" ph fetch \
    --paper-id arxiv://$ARXIV_ID --include-content \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"][0]["full_text_path"])')
PAPER_DIR=$(dirname "$FULL_MD")
echo "Paper dir: $PAPER_DIR"
ls "$PAPER_DIR/"
ls "$PAPER_DIR/images/" 2>/dev/null | wc -l
```

> ⚠️ **不要**用 `tr '.' '_'` 手动拼接路径——实际目录名用点号（如 `arxiv_2603.16060`），手动拼接与实际不符。始终从 `full_text_path` 推导。

## 图片落地验证

```bash
IMG_COUNT=$(ls "$PAPER_DIR/images/" 2>/dev/null | wc -l)
echo "Images found: $IMG_COUNT"

if [ "$IMG_COUNT" -eq 0 ]; then
    echo "⚠️  images/ 目录为空，重新触发..."
    uv run --project "$HOME/project/ph2" ph fetch --paper-id arxiv://$ARXIV_ID --force
    until uv run --project "$HOME/project/ph2" ph fetch \
        --paper-id arxiv://$ARXIV_ID 2>&1 | grep -q '"fetch_state": "done"'; do
        sleep 15
    done
    IMG_COUNT=$(ls "$PAPER_DIR/images/" 2>/dev/null | wc -l)
    echo "Images after retry: $IMG_COUNT"
fi
```

## 解析图片顺序（仅 full.md 引用的图片）

**只处理 `full.md` 中出现的图片引用**，`images/` 目录中未被引用的文件（MinerU 中间裁切图等）不要插入。

```python
import re

full_md_path = f"{PAPER_DIR}/full.md"
with open(full_md_path) as f:
    content = f.read()

# 只提取 full.md 中实际引用的图片，按出现顺序
img_refs = re.findall(r'!\[\]\(images/([a-f0-9]+\.(?:jpg|png))\)', content)

# 找每张图片后紧跟的 Figure caption
figures = []
for i, fname in enumerate(img_refs):
    pos = content.find(f"images/{fname}")
    excerpt = content[pos:pos+500]
    fig_match = re.search(r'Figure\s+(\d+)[:\.]?\s*([^\n]+)', excerpt)
    if fig_match:
        fig_num = fig_match.group(1)
        caption_en = fig_match.group(2).strip()
        figures.append((fname, fig_num, caption_en))
    else:
        figures.append((fname, str(i+1), ""))

print(f"full.md 引用图片: {len(img_refs)} 张（images/ 目录总计可能更多，忽略未引用的）")
for fname, num, cap in figures:
    print(f"  fig{num}: {fname} | {cap[:60]}")
```

## 获取全文内容

```bash
uv run --project "$HOME/project/ph2" ph fetch \
    --paper-id arxiv://$ARXIV_ID --include-content \
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
- `images/` 目录图片数量通常**多于** `full.md` 引用数量（含附录图、表格截图、MinerU 裁切图），**只按 full.md 引用顺序插入**
- 翻译时用 `full.md` 内容（有正确的图片占位），不要用 Jina/arxiv HTML
- 如果 `PH_MINERU_TOKEN` 未配置，MinerU 不可用，降级为纯文本翻译（无图）
