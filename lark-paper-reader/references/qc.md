# qc.md — 质量检查程序

完成所有注释操作后，运行以下检查。**有任何 ISSUE 都必须修复后再交付。**

---

## 完整 QC 脚本

```python
#!/usr/bin/env python3
"""
用法：python3 qc.py <document_id>
"""
import json, re, subprocess, sys
from collections import Counter

DOC = sys.argv[1] if len(sys.argv) > 1 else input("Document ID: ").strip()

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))
    return r.stdout + r.stderr

issues = []

# ── 1. 图片检查 ──
print("1. 检查图片...")
out = run(["lark-cli","docs","+fetch","--api-version","v2","--doc",DOC,
           "--detail","full","--doc-format","xml","--as","user"])
try:
    c = json.loads(out)["data"]["document"]["content"]
except:
    print("  WARN: 无法解析文档内容")
    c = ""

imgs = re.findall(r'<img[^>]+>', c)
srcs = [re.search(r'src="([^"]+)"',i).group(1) for i in imgs if re.search(r'src=',i)]
names = [re.search(r'name="([^"]+)"',i).group(1) for i in imgs if re.search(r'name=',i)]
src_cnt, name_cnt = Counter(srcs), Counter(names)
dup_srcs = [s for s,n in src_cnt.items() if n>1]
dup_names = [nm for nm,n in name_cnt.items() if n>1]

print(f"   图片总数: {len(imgs)}")
for nm in dup_names:
    # 找重复的 block_id
    dup_blocks = re.findall(r'<img[^>]*name="{}"[^>]*id="([^"]+)"'.format(re.escape(nm)), c)
    issues.append({"type":"dup_image","name":nm,"blocks":dup_blocks})
    print(f"   !! 重复图片: {nm} ({len(dup_blocks)} 个 block)")
    print(f"      block_ids: {dup_blocks}")
    print(f"      修复: lark-cli docs +update --doc {DOC} --command block_delete --block-id {dup_blocks[-1]} --as user")

# ── 2. H3 标题重复检查 ──
print("2. 检查重复标题...")
h3s = re.findall(r'<h3[^>]*>([^<]+)</h3>', c)
h3_cnt = Counter(h3s)
dup_h3 = [(h,n) for h,n in h3_cnt.items() if n>1]
if dup_h3:
    for h,n in dup_h3:
        issues.append({"type":"dup_h3","title":h,"count":n})
        print(f"   !! 重复标题 ({n}x): {h}")
else:
    print(f"   OK ({len(h3s)} 个标题，无重复)")

# ── 3. 段落重复检查 ──
print("3. 检查重复段落...")
paras = re.findall(r'<p[^>]*>([^<]{60,})</p>', c)
para_cnt = Counter(paras)
dup_paras = [(p,n) for p,n in para_cnt.items() if n>1]
if dup_paras:
    for p,n in dup_paras[:3]:
        issues.append({"type":"dup_para","text":p[:60],"count":n})
        print(f"   !! 重复段落 ({n}x): {p[:60]}")
else:
    print(f"   OK")

# ── 4. Comment 重复检查 ──
print("4. 检查重复评论...")
out2 = run(["lark-cli","drive","file.comments","list",
            "--params", json.dumps({"file_token":DOC,"file_type":"docx","is_whole":False,"page_size":100}),
            "--as","user"])
try:
    comments_data = json.loads(out2)
    all_comments = comments_data.get("data",{}).get("items",[])
    texts = []
    id_map = {}
    for item in all_comments:
        cid = item.get("comment_id","")
        for reply in item.get("reply_list",{}).get("replies",[]):
            for elem in reply.get("content",{}).get("elements",[]):
                t = elem.get("text_run",{}).get("text","")
                if t:
                    texts.append(t)
                    id_map.setdefault(t[:80], []).append(cid)

    text_cnt = Counter(t[:80] for t in texts)
    dup_comments = [(t,n) for t,n in text_cnt.items() if n>1]
    print(f"   评论总数: {len(texts)}")
    for t,n in dup_comments:
        cids = id_map.get(t,[])
        issues.append({"type":"dup_comment","text":t[:60],"ids":cids})
        print(f"   !! 重复评论 ({n}x): {t[:50]}")
        print(f"      修复（关闭其中一个）:")
        if cids:
            print(f"      lark-cli drive file.comments patch --params '{{\"file_token\":\"{DOC}\",\"file_type\":\"docx\",\"comment_id\":\"{cids[-1]}\"}}' --data '{{\"is_solved\":true}}' --as user")
except:
    print("   WARN: 无法获取评论列表")

# ── 5. 章节完整性 ──
print("5. 检查章节完整性...")
out3 = run(["lark-cli","docs","+fetch","--api-version","v2","--doc",DOC,
            "--doc-format","markdown","--as","user"])
try:
    md_c = json.loads(out3)["data"]["document"]["content"]
    for section in ["摘要","引言","方法","实验","结论"]:
        found = section in md_c
        print(f"   {'✓' if found else '✗ MISSING'} {section}")
        if not found:
            issues.append({"type":"missing_section","section":section})
except:
    print("   WARN: 无法解析 markdown 内容")

# ── 汇总 ──
print()
if issues:
    print(f"⚠️  发现 {len(issues)} 个问题，请修复后重新交付")
    for iss in issues:
        print(f"  - [{iss['type']}] {str(iss)[:80]}")
else:
    print("✅ QC 通过，文档质量良好")
```

---

## 快速修复命令

```bash
DOC="<document_id>"

# 删除重复图片 block
lark-cli docs +update --doc $DOC \
  --command block_delete --block-id <dup_block_id> --as user

# 关闭重复评论
lark-cli drive file.comments patch \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"comment_id\":\"<id>\"}" \
  --data '{"is_solved":true}' --as user

# 删除重复 callout block（先用 with-ids fetch 找 block_id）
lark-cli docs +fetch --doc $DOC \
  --detail with-ids --scope keyword --keyword "<callout标题>" \
  --doc-format xml --as user
# 然后 block_delete
```

---

## 交付标准

| 检查项 | 合格标准 |
|--------|---------|
| 图片 | 每张论文图仅出现一次，有中文 caption |
| H3 标题 | 无重复 |
| 评论 | 无重复内容（内容 >60 字符的评论） |
| 章节 | 摘要/引言/方法/实验/结论均在 |
| 附录 | 若原论文有实验表格/案例/伪代码，必须出现在文档末尾 |
