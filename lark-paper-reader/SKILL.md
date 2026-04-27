---
name: lark-paper-reader
version: 1.0.0
description: "将学术论文（arXiv/DOI）全自动处理为飞书注释文档：ph+MinerU获取带图全文 → 中文翻译 → 创建飞书文档（统一文件夹）→ 插入原始图片 → 添加公式推导callout/段落摘要comment/术语注释 → 展开关键参考文献 → 自动质量检查（去重复图片/评论）。触发语境：'帮我读/翻译这篇论文'、'上传到飞书'、'arxiv://xxx 注释'、'给这篇paper做笔记'。"
metadata:
  requires:
    bins: ["lark-cli"]
    skills: ["lark", "ph-paper-helper"]
---

# lark-paper-reader

将一篇论文变成一份**可直接阅读的飞书注释文档**：中文翻译 + 原图 + 公式推导 + 术语解释 + 参考文献展开，全部自动完成，最终存入统一的飞书文件夹。

## 前置条件

本 skill 依赖两个已有 skill，**请先确认它们已就绪**：

1. **[`lark`](../lark/SKILL.md)**：飞书认证、文档操作、Drive 上传。执行 `lark-cli auth status` 确认已登录，所需 scope 见 lark skill § 0。
2. **[`ph-paper-helper`](../ph-paper-helper/SKILL.md)**：论文导入与 MinerU 全文解析。`PH_MINERU_TOKEN` 等环境变量配置见 ph-paper-helper skill 的「环境变量」一节。

```bash
lark-cli auth status   # 确认飞书已登录
ph --version           # 确认 ph 可用（alias ph='uv run --project ~/project/ph2 ph'）
```

## 输入解析

接受以下任意格式：
- arXiv ID：`2604.14010` 或 `arxiv://2604.14010`
- arXiv URL：`https://arxiv.org/abs/2604.14010`
- DOI：`doi://10.48550/arXiv.2604.14010`

统一转为 `ph` URI 格式（`arxiv://ID` 或 `doi://XXX`）再处理。

## 工作流总览

```
输入论文 ID/URL
     │
     ▼
Step 1  ph import + ph fetch --force   ← MinerU 解析 PDF，获取带图 Markdown
     │   等待 fetch_state=done
     ▼
Step 2  翻译正文                        ← 中文翻译，写入 /tmp/<arxiv_id>_zh.md
     │
     ▼
Step 3  lark-cli docs +create          ← 在飞书统一文件夹创建文档
     │   --parent-token <FOLDER_TOKEN>
     ▼
Step 4  插入图片                        ← 逐张 docs +media-insert
     │   从 full.md 的 images/ 目录读取
     ▼
Step 5  添加注释层                      ← 详见 references/annotate.md
     │   callout（公式/直觉/引用）
     │   comment（术语/段落摘要）
     ▼
Step 6  展开关键参考文献                ← ph fetch 被引论文，inline callout
     │
     ▼
Step 7  质量检查                        ← 详见 references/qc.md
         检测重复图片/评论/callout
```

---

## Step 1：获取带图全文

```bash
# 导入（自动拉取纯文本）
ph import --input arxiv://2604.14010

# 触发 MinerU（获取带图 Markdown）
ph fetch --paper-id arxiv://2604.14010 --force

# 轮询等待完成
until ph fetch --paper-id arxiv://2604.14010 2>&1 | grep -q '"fetch_state": "done"'; do
  sleep 15
done

# 获取带图内容
ph fetch --paper-id arxiv://2604.14010 --include-content
```

MinerU 完成后检查：
```bash
PAPER_DIR=~/.local/share/ph/papers/arxiv_<ID>
ls $PAPER_DIR/           # 应有 full.md + images/ 目录
ls $PAPER_DIR/images/    # 若为空则说明第一次 fetch 有问题，--force 重跑
```

> **如果 images/ 目录为空**：说明 MinerU 结果未同步，执行 `ph fetch --force` 重新触发。详见 [references/fetch.md](references/fetch.md)。

---

## Step 2：翻译

逐节翻译，保留：
- 所有公式（原样保留 LaTeX，不翻译符号）
- 图表位置标记（`[图X位置]` 占位，稍后由 Step 4 替换为实际图片）
- 节标题层级

翻译原则：
- 核心术语首次出现保留英文（如"Evolving Parameter Isolation (EPI)"翻译为"演化参数隔离（EPI）"）
- 不压缩信息，逐节完整翻译，不跳过附录
- 附录若有实验表格、案例对比、算法伪代码，**必须全部翻译包含**

存为临时文件：
```bash
# 写入 /tmp/<arxiv_id>_zh.md，分多次写入避免超限
```

---

## Step 3：创建飞书文档

统一存放在固定文件夹（`PAPER_FOLDER_TOKEN`）：

```bash
# 默认文件夹 token（论文阅读统一文件夹）
FOLDER="fldcnqoIiMr6t2atnEfFBpxksRd"   # 按实际配置

cd /tmp && lark-cli docs +create \
  --api-version v2 \
  --title "【译文】<论文标题> | arXiv <ID>" \
  --doc-format markdown \
  --content @<arxiv_id>_zh.md \
  --parent-token "$FOLDER" \
  --as user
```

记录返回的 `document_id`，后续所有操作均使用此 ID。

> 如果没有固定文件夹 token，使用 `--parent-position my_library` 存到个人文档库，之后手动移动。

---

## Step 4：插入图片

从 MinerU 的 `images/` 目录读取图片，按 `full.md` 中出现顺序逐张插入：

```bash
PAPER_DIR=~/.local/share/ph/papers/arxiv_<ID>
DOC=<document_id>

# 解析 full.md 中的图片顺序和对应 caption（在紧接的 Figure X: 行提取）
# 对每张图片：
cd /tmp && lark-cli docs +media-insert \
  --doc "$DOC" \
  --file "$PAPER_DIR/images/<hash>.jpg" \
  --caption "<图X：论文图注中文翻译>" \
  --selection-with-ellipsis "<图片前后唯一定位文本>" \
  --align center \
  --as user
```

图片定位策略：
1. 优先用图片**之前**的段落末句作为 `--selection-with-ellipsis` 的锚点
2. 若段落文字在文档中有歧义（多次出现），改用 `start...end` 省略号语法唯一定位
3. 插入后立即验证（检查返回的 block_id 是否正常）

详细流程见 [references/images.md](references/images.md)。

---

## Step 5：添加注释层

按三层结构添加注释，**不要在数量上做压缩**：

### 5a. 导读块（文档开头）

在标题/副标题之后插入 `block_insert_after`：

```xml
<callout emoji="📍" background-color="light-blue" border-color="blue">
  <h3>导读指南</h3>
  <p><b>核心问题：</b>...</p>
  <p><b>作者答案：</b>...</p>
  <h3>预备知识速查</h3>
  <li><b>关键术语1</b>：...</li>
  ...
</callout>
```

### 5b. Callout 块（内联注释，插在各位置后）

触发位置和类型，详见 [references/annotate.md](references/annotate.md)：

| emoji | 类型 | 插入时机 |
|-------|------|---------|
| 💡 | 公式推导/直觉解释 | 每个重要公式块之后 |
| 📖 | 引用背景 | 引用重要相关工作时 |
| 🔧 | 实现要点 | 算法/伪代码段落之后 |
| ❓ | 读者常见疑问 | 每个主要节末尾 |

### 5c. Comment（边注，不打断阅读）

```python
# content 必须是 JSON
content_json = json.dumps([{"type": "text", "text": "注释内容"}], ensure_ascii=False)
subprocess.run(["lark-cli", "drive", "+add-comment",
    "--doc", DOC, "--type", "docx",
    "--selection-with-ellipsis", "<唯一定位文本>",
    "--content", content_json, "--as", "user"])
```

触发时机：
- **术语出现**：每个专业术语第一次出现时 → 简短定义
- **长段**（>3句，无子标题）：段首/段尾 → `【段落摘要】...`

---

## Step 6：展开关键参考文献（1-hop）

识别论文中被**直接对比或作为理论基础**的关键引用（通常 3-5 篇），用 ph 获取全文，inline 插入 callout：

```bash
# 搜索并导入被引论文
ph search --query "<标题关键词>" --max-results 3
ph fetch --paper-id <paper_id> --include-content
```

**只展开高价值引用**（被引用超过 2 次、或在方法对比中出现）。展开格式：

```xml
<callout emoji="📖" background-color="light-green" border-color="green">
  <h3>被引文献：Wang et al. 2025 — 本文最重要的对比基线</h3>
  <p><b>论文：</b>标题</p>
  <p><b>核心思路：</b>...</p>
  <p><b>与本文的关系：</b>...</p>
</callout>
```

---

## Step 7：质量检查

完成后执行自动检查，详见 [references/qc.md](references/qc.md)：

```bash
DOC=<document_id>

# 1. 获取 XML 全文，统计图片
lark-cli docs +fetch --api-version v2 --doc $DOC --detail full --doc-format xml --as user \
  | python3 -c "
import json,sys,re
from collections import Counter
c=json.loads(sys.stdin.read())['data']['document']['content']
imgs=re.findall(r'<img[^>]+>',c)
srcs=[re.search(r'src=\"([^\"]+)\"',i).group(1) for i in imgs if re.search(r'src=',i)]
names=[re.search(r'name=\"([^\"]+)\"',i).group(1) for i in imgs if re.search(r'name=',i)]
cnt=Counter(names)
print(f'Images: {len(imgs)}')
for nm,n in cnt.items():
    if n>1: print(f'!! DUPLICATE: {nm}')
# 检查 H3 重复
h3s=re.findall(r'<h3[^>]*>([^<]+)</h3>',c)
hcnt=Counter(h3s)
for h,n in hcnt.items():
    if n>1: print(f'!! DUPLICATE H3: {h}')
print('OK' if not any(n>1 for n in cnt.values()) else 'ISSUES FOUND')
"

# 2. 获取所有评论，检查重复
lark-cli drive file.comments list \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"is_whole\":false,\"page_size\":100}" \
  --as user \
  | python3 -c "
import json,sys
from collections import Counter
d=json.load(sys.stdin)
texts=[]
for c in d.get('data',{}).get('items',[]):
    for r in c.get('reply_list',{}).get('replies',[]):
        for e in r.get('content',{}).get('elements',[]):
            t=e.get('text_run',{}).get('text','')
            if t: texts.append(t[:60])
cnt=Counter(texts)
dups=[(t,n) for t,n in cnt.items() if n>1]
print(f'Comments: {len(texts)}, Duplicates: {len(dups)}')
for t,n in dups:
    print(f'!! DUPLICATE ({n}x): {t}')
"
```

**修复重复**：
```bash
# 删除重复图片 block
lark-cli docs +update --api-version v2 --doc $DOC \
  --command block_delete --block-id <dup_block_id> --as user

# 将重复评论标记为 resolved
lark-cli drive file.comments patch \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"comment_id\":\"<id>\"}" \
  --data '{"is_solved":true}' --as user
```

---

## 前置配置（由各 skill 负责）

- **飞书认证 & 文件夹**：由 [`lark`](../lark/SKILL.md) 管理。确认已 `lark-cli auth status`，目标文件夹 token 通过飞书网页端 URL 获取（`/drive/folder/<token>`），传入 Step 3 的 `--parent-token`。
- **MinerU token（`PH_MINERU_TOKEN`）**：由 [`ph-paper-helper`](../ph-paper-helper/SKILL.md) 管理。未配置时 `ph fetch` 无法解析 PDF 图片，降级为纯文本模式。

---

## 错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| `images/` 目录为空 | 第一次 MinerU 结果未落地 | `ph fetch --force` 重新触发 |
| `selection-with-ellipsis` 找不到 | 文本在 callout 里已出现 | 换用更唯一的上下文文本或 `block_id` |
| comment 重复 | 相同 selection 成功两次 | `file.comments patch is_solved=true` 关闭其中一个 |
| 图片重复 | `+media-insert` 执行了两次 | `docs +update block_delete` 删除多余 block |
| `--content` JSON 报错 | shell 引号问题 | 用 `python3` 生成 JSON 再传给 subprocess |
