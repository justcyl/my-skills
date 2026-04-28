# images.md — 图片插入详细流程

## 准备工作

在翻译文档中，需要为每张图片确定：
1. **文件名**：`<hash>.jpg`（相对于 `$PAPER_DIR/images/`）
2. **中文 caption**：翻译论文图注（"Figure X: ..."）
3. **定位锚点**：图片前后的唯一文字，用于 `--selection-with-ellipsis`

> ⚠️ `lark-cli docs +media-insert --file` 只接受**相对于当前目录的路径**，绝对路径会报 `unsafe file path` 错误。
> 正确做法：先 `cd "$PAPER_DIR/images"`，再用文件名。

## 逐张插入

```python
import subprocess, json, os

DOC = "<document_id>"
PAPER_DIR = "<从 ph fetch full_text_path 推导，见 fetch.md>"

# 切换到 images 目录，之后 --file 只需文件名
os.chdir(f"{PAPER_DIR}/images")

# 按 full.md 引用顺序定义图片列表（不要插入 full.md 未引用的图片）
figures = [
    {
        "file": "<hash1>.jpg",       # 相对路径，无需目录前缀
        "caption": "图1：<中文图注>",
        "selection": "<图片前的唯一段落文字，20-40字>",
        "before": False,
    },
    # ...
]

for fig in figures:
    result = subprocess.run(
        ["lark-cli", "docs", "+media-insert",
         "--doc", DOC,
         "--file", fig["file"],
         "--caption", fig["caption"],
         "--selection-with-ellipsis", fig["selection"],
         "--align", "center",
         "--as", "user"]
        + (["--before"] if fig.get("before") else []),
        capture_output=True, text=True
    )
    # +media-insert 输出混有日志行，不能直接 json.loads 整体输出
    # 优先用 returncode 判断成功，再从输出中提取 JSON
    if result.returncode == 0:
        block_id = "?"
        for line in (result.stdout + result.stderr).strip().split("\n"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    d = json.loads(line)
                    block_id = d.get("data", {}).get("block_id", "?")
                    break
                except json.JSONDecodeError:
                    pass
        print(f"✓ {fig['caption'][:30]} -> block {block_id}")
    else:
        print(f"✗ {fig['caption'][:30]}: {(result.stdout + result.stderr)[:120]}")
```

## 定位锚点选择

优先级（从高到低）：

1. **图片前的段落末句**（最稳定）：
   ```
   selection = "因此，静态隔离机制不可避免地与学习轨迹脱节"
   ```

2. **图片后的段落首句**（配合 `--before`）：
   ```
   selection = "我们认为这一静态假设与SFT高度动态的本质相悖"
   before = True
   ```

3. **唯一节标题**：
   ```
   selection = "## 2. 方法论"  # 用于在节首插入
   before = True
   ```

4. **`start...end` 消歧**（当短文本不唯一时）：
   ```
   selection = "为解决这一困境...使其暴露在后续更新的覆写风险中"
   ```

## 处理 ambiguous_match

当 `+media-insert` 报 `ambiguous_match` 时：

```bash
# Step 1: 用 keyword scope 找目标 block 的 ID
lark-cli docs +fetch --api-version v2 --doc $DOC \
  --detail with-ids --scope keyword --keyword "<部分定位文字>" \
  --doc-format xml --as user \
  | python3 -c "
import json,sys,re
c=json.loads(sys.stdin.read())['data']['document']['content']
ids=re.findall(r'id=\"(doxcn[^\"]+)\"',c)
texts=re.findall(r'>\s*([^\<]{10,60})',c)
for bid,txt in zip(ids,texts):
    print(bid,'|',txt[:50])
"

# Step 2: 用 block_insert_after 精确定位
lark-cli docs +update --api-version v2 --doc $DOC \
  --command block_insert_after \
  --block-id <target_block_id> \
  --content '<img...>' \    # 注意：+media-insert 有4步编排，直接用 update 需手动上传
  --as user
```

> 更简单的做法：把图片 append 到文档末尾，然后手动在飞书拖动到正确位置。

## 验证插入结果

```bash
lark-cli docs +fetch --api-version v2 --doc $DOC \
  --detail full --doc-format xml --as user \
  | python3 -c "
import json,sys,re
c=json.loads(sys.stdin.read())['data']['document']['content']
imgs=re.findall(r'<img[^>]+>',c)
print(f'Total images: {len(imgs)}')
for img in imgs:
    name=re.search(r'name=\"([^\"]+)\"',img)
    cap=re.search(r'caption=\"([^\"]+)\"',img)
    print(f'  {name.group(1) if name else \"?\"} | {(cap.group(1) if cap else \"?\")[:60]}')
"
```
