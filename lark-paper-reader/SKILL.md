---
name: lark-paper-reader
description: "将学术论文（arXiv/DOI）全自动处理为飞书注释文档。触发语境：'帮我读/翻译这篇论文'、'上传到飞书'、'arxiv://xxx 注释'、'给这篇paper做笔记'。"
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
uv run --project ~/project/ph2 ph --version           # 确认 ph 可用（alias ph='uv run --project ~/project/ph2 ph'）
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
     │   分多次写入避免工具超限
     ▼
Step 3  lark-cli docs +create          ← 在飞书统一文件夹创建文档
     │   --parent-token <FOLDER_TOKEN>
     ▼
Step 4  插入图片 + 删除占位符           ← 逐张 docs +media-insert
     │   插入后 block_delete 占位符块
     ▼
Step 5  添加注释层 + 附录内容前置       ← 详见 references/annotate.md
     │   callout（公式/直觉/引用/代码）
     │   comment（术语/段落摘要）
     │   附录有助于理解正文时 → 提前为 callout，原位省略
     ▼
Step 5.5  代码仓库集成（可选）          ← 论文有开源代码时执行
     │   克隆仓库 → 阅读核心模块 → 以 callout 内嵌代码块注入文档
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

MinerU 完成后，从返回结果推导 `PAPER_DIR`（**不要手动拼路径**）：
```bash
# 从 ph fetch 返回的 full_text_path 推导目录，兼容 dot/underscore/版本后缀
FULL_MD=$(uv run --project "$HOME/project/ph2" ph fetch \
  --paper-id arxiv://$ARXIV_ID --include-content \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"][0]["full_text_path"])')
PAPER_DIR=$(dirname "$FULL_MD")
echo "Paper dir: $PAPER_DIR"
ls "$PAPER_DIR/"          # 应有 full.md + images/ 目录
ls "$PAPER_DIR/images/"   # 若为空则说明第一次 fetch 有问题，--force 重跑
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
- 不压缩信息，逐节完整翻译
- 附录**按需前置**（见 Step 5 § 5d）：若附录某节（实验超参、案例、算法伪代码等）能帮助读者及时理解正文，Step 5 阶段以 callout 形式提前插入正文对应位置，该附录节在原位可保留摘要或省略；不涉及正文理解的附录节仍完整翻译在末尾

存为临时文件，**分多次写入**避免 write 工具超限：
```bash
# 第1块：用 write 工具写入标题+摘要+第1节（约80-100行）
# 第2块起：用 bash append 追加
cat >> /tmp/<arxiv_id>_zh.md << 'CHUNKN'
...下一段译文...
CHUNKN
echo "当前行数：$(wc -l < /tmp/<arxiv_id>_zh.md)"
```

> 每块约 80–120 行（约 3000 字），结束后打印当前行数确认写入成功。

---

## Step 3：创建飞书文档

统一存放在固定文件夹（`PAPER_FOLDER_TOKEN`）：

```bash
# 首选：存到个人文档库，之后可在飞书里手动移动到目标文件夹
cd /tmp && lark-cli docs +create \
  --api-version v2 \
  --title "【译文】<论文标题> | arXiv <ID>" \
  --doc-format markdown \
  --content @<arxiv_id>_zh.md \
  --parent-position my_library \
  --as user

# 如果有固定文件夹 token（从飞书网页 URL /drive/folder/<token> 获取）：
# cd /tmp && lark-cli docs +create \
#   --api-version v2 \
#   --title "【译文】<论文标题> | arXiv <ID>" \
#   --doc-format markdown \
#   --content @<arxiv_id>_zh.md \
#   --parent-token "<FOLDER_TOKEN>" \
#   --as user
```

---

## Step 4：插入图片

**只插入 `full.md` 中实际引用的图片**，`images/` 目录中未被引用的文件（MinerU 中间裁切图、附录图等）一律不插。

```bash
PAPER_DIR=<从 Step 1 得到的目录>
DOC=<document_id>

# 先解析 full.md 中的图片引用顺序（见 references/fetch.md § 解析图片顺序）
# 对每张 full.md 引用的图片：
cd "$PAPER_DIR/images"    # 必须先 cd 到 images 目录
lark-cli docs +media-insert \
  --doc "$DOC" \
  --file "<hash>.jpg" \
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

### 插入后删除占位符

图片插入完毕后，**必须删除**翻译时写入的 `[图X位置]` 占位符块，否则文档中会出现裸文字残留：

```bash
DOC=<document_id>

# 一次性找出所有占位符 block 并删除
lark-cli docs +fetch --api-version v2 --doc "$DOC" --detail full --doc-format xml --as user \
  > /tmp/lark_placeholders.json

python3 -c "
import json, re
with open('/tmp/lark_placeholders.json') as f:
    content = json.load(f)['data']['document']['content']
matches = re.findall(r'id=\"(doxcn[^\"]+)\">(\[图\d+位置\])<', content)
for bid, text in matches:
    print(f'{bid}  {text}')
"
# 对每个返回的 block_id 执行：
lark-cli docs +update --api-version v2 --doc "$DOC" \
  --command block_delete --block-id <placeholder_block_id> --as user
```

---

## Step 5：添加注释层

按三层结构添加注释。**覆盖率要求见 [references/annotate.md](references/annotate.md)，必须先建立扫描列表再逐元素处理。**

### 5-PRE. 建立待处理列表（必须先做）

Step 5 正式开始前，fetch 文档 XML，提取所有需要标注的元素，建立清单后再逐一处理：

```bash
DOC=<document_id>

# 先将输出存文件，再用 python3 heredoc 处理（pipe + heredoc 会导致 stdin 冲突）
lark-cli docs +fetch --api-version v2 --doc "$DOC" --detail full --doc-format xml --as user \
  > /tmp/lark_doc_scan.json

python3 << 'EOF'
import json, re

with open('/tmp/lark_doc_scan.json') as f:
    content = json.load(f)['data']['document']['content']

# 章节列表（用于确认 ❓ callout 覆盖）
sections = re.findall(r'<h[23][^>]*id="(doxcn[^"]+)"[^>]*>([^<]+)<', content)
print("=== 章节 ===")
for bid, title in sections:
    print(f"  [{bid}] {title}")

# 长段落（>80字，用于确认 comment 覆盖）
long_ps = re.findall(r'<p[^>]*id="(doxcn[^"]+)"[^>]*>(.{80,}?)</p>', content, re.DOTALL)
print(f"\n=== 长段落: {len(long_ps)} 个 ===")
for bid, text in long_ps[:5]:
    print(f"  [{bid}] {text[:50].strip()}...")
print(f"  (共 {len(long_ps)} 个，需逐一加 comment)")
EOF
```

把输出结果逐条处理，**处理完一个在列表里划掉一个**，不允许凭印象跳过。

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

覆盖率硬性要求和每类 callout 的格式，详见 [references/annotate.md](references/annotate.md)。

| emoji | 类型 | 插入时机 |
|-------|------|---------|
| 💡 | 公式推导/直觉解释 | 方法章节每个公式块之后（必须，无例外） |
| 🌉 | 具象化示例 | 每个抽象方法步骤/阶段描述之后（见 annotate.md § 🌉） |
| 📖 | 引用背景 | 被引用 ≥2 次或作为对比 baseline 的文献首次出现时 |
| 🔧 | 实现要点 | 每个算法框/伪代码块之后（含代码块） |
| ❓ | 读者常见疑问 | 每个 §实验/§消融/§分析 节末尾 |

**🔧 类型的 callout 可以内嵌代码块**，将说明和代码封装在同一视觉容器（具体语法见 Step 5.5 § 3）。

`block_replace` 支持一次替换为多个顶层块，可用来把「旧 callout」替换为「新 callout + 独立 pre 块」，或直接替换为「含 pre 的 callout」：

```bash
# 将 OLD_CALLOUT_ID 替换为：新 callout（含嵌入代码块）
lark-cli docs +update --api-version v2 --doc "$DOC" \
  --command block_replace \
  --block-id "OLD_CALLOUT_ID" \
  --content '<callout emoji="🔧" background-color="light-gray" border-color="gray">
<h3>标题</h3>
<p>说明文字</p>
<pre lang="python"><code>代码内容</code></pre>
</callout>' \
  --doc-format xml --as user
```

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

### 5d. 附录内容前置

阅读附录时，判断每个附录节是否**有助于读者在阅读正文时就能更好理解内容**：

| 附录类型 | 建议 | 实例 |
|----------|------|------|
| 算法伪代码 / 训练细节 | 前置到方法节末尾 | Prompt 模板、超参表：方法节末 |
| 案例分析 / 定性结果 | 前置到实验节末尾 | 验证案例：实验分析节末 |
| 推导细节 / 证明过程 | 前置到对应公式后 | 公式完整推导：公式所在段辺 |
| 补充实验 / 边界情况 | 前置到实验节末尾（如果正文已深入探讨） | 参数敏感性分析：对应结果表边 |
| 相关工作详述 / 统计表 | **保留在附录**，正文不需要 | 达到类似结论的相关工作列表 |

**前置格式**：使用淡紫色 callout，标注来源于哪个附录节：

```xml
<callout emoji="📌" background-color="light-purple" border-color="purple">
  <h3>【附录 B.1 前置】算法伪代码：XXX 训练全流程</h3>
  <p>此内容原位于附录 B.1，提前展示以助理解上方公式。</p>
  <!-- 附录原内容 -->
</callout>
```

附录节原位可添加简短说明：「本节内容已前置至正文§X.X 节末」并省略详细内容；与正文理解无关的附录节仍按原样完整翻译。

---

## Step 5.5：代码仓库集成（可选）

若论文摘要或 Introduction 中出现 GitHub 链接，或 abstract 含「code is available」字样，在 Step 5 完成后执行本步骤。

### 1. 克隆仓库

```bash
GITHUB_URL="https://github.com/<org>/<repo>"   # 从论文中提取
cd /tmp && git clone --depth 1 "$GITHUB_URL" paper_code 2>&1 | tail -3
find /tmp/paper_code -name "*.py" | grep -v __pycache__ | sort | head -40
```

### 2. 建立代码架构地图（先于阅读任何文件）

**在阅读任何代码文件之前**，先在文档开头（导读块之后）插入一个架构地图 callout。这是读者进入代码时的「地图」，让孤立的代码片段有了定位感。

```bash
# 生成目录树
find /tmp/paper_code -name "*.py" | grep -v __pycache__ | sort | head -30
# 找核心模块（内存/技能/策略等）
find /tmp/paper_code -name "*.py" | xargs grep -l "class.*Memory\|class.*Skill\|def.*distill\|def.*evolve" 2>/dev/null
```

用 `read` 工具逐一阅读关键文件后，在文档中插入架构地图：

```xml
<callout emoji="🗺️" background-color="light-blue" border-color="blue">
<h3>代码仓库架构地图</h3>
<p><b>仓库：</b>github.com/org/repo</p>
<p><b>阅读顺序：</b>按下面的顺序读，每个文件负责论文的哪个部分一目了然</p>
<li><b>path/to/core.py</b>：对应论文 §3.1，核心数据结构（技能/记忆定义）</li>
<li><b>path/to/train.py</b>：对应论文 §3.2，训练主循环（调用 core.py）</li>
<li><b>path/to/retrieve.py</b>：对应论文 §3.3，检索/更新逻辑</li>
<p><b>数据流（一次训练步骤）：</b></p>
<p>输入样本 → train.py:step() → core.py:update() → retrieve.py:lookup() → 输出梯度</p>
<p><b>忽略这些文件（框架胶水代码）：</b>trainer/, verl/, utils/logging.py</p>
</callout>
```

### 3. 定位关键实现文件并插入代码 callout

对应正文中每个关键方法步骤（公式、算法伪代码），在其后用 `block_insert_after` 或 `block_replace` 插入代码 callout。

**每个代码 callout 必须包含三部分**：①论文公式/步骤的映射说明，②带行内注释的代码，③前置条件和后置结果（代码调用这个函数时「进来是什么状态」「出去是什么状态」）：

```xml
<callout emoji="🔧" background-color="light-gray" border-color="gray">
<h3>代码：函数名（path/to/file.py）</h3>
<p><b>对应论文：</b>公式(3) / Algorithm 1 第2行 / §3.2 第二段</p>
<p><b>调用前状态：</b>输入是 X（形状/类型），上下文变量 Y 已初始化</p>
<pre lang="python"><code>def key_function(x, context):
    # Step 1: 对应论文公式(3)左半部分——计算 Q
    q = self.query_proj(x)          # [B, D]
    # Step 2: 对应论文公式(3)右半部分——检索 K
    scores = torch.einsum('bd,nd->bn', q, context.keys)  # [B, N]
    # Step 3: 对应论文中的 softmax 归一化
    weights = F.softmax(scores / self.temp, dim=-1)      # [B, N]
    return weights @ context.values  # 输出 [B, D]</code></pre>
<p><b>调用后状态：</b>返回聚合后的值向量，用于后续的残差连接</p>
</callout>
```

若有多段代码，在同一 callout 内放多个 `<pre>` 即可。关键语法：

> ✅ `<pre lang="python"><code>...</code></pre>` 可直接嵌入 `<callout>` 内，生成带语法高亮的代码块。
> ❌ `<p><code>...</code></p>` 是行内等宽字体，**不要用**。

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

# 0. 覆盖率检查（先存文件再处理，避免 pipe+heredoc stdin 冲突）
lark-cli docs +fetch --api-version v2 --doc $DOC --detail full --doc-format xml --as user \
  > /tmp/lark_qc.json

python3 << 'EOF'
import json, re
from collections import Counter

with open('/tmp/lark_qc.json') as f:
    c = json.load(f)['data']['document']['content']

callout_emojis = re.findall(r'emoji="([^"]+)"', c)
for emoji, label in [('💡','公式推导'), ('🌉','具象化'), ('❓','读者疑问'), ('📖','引用背景'), ('🔧','代码')]:
    print(f"{emoji} {label}: {callout_emojis.count(emoji)}")

long_paras = re.findall(r'<p[^>]*>(.{80,}?)</p>', c, re.DOTALL)
print(f"长段落数(需 comment): {len(long_paras)}")

if callout_emojis.count('🌉') == 0:
    print("!! WARNING: 没有任何 🌉 具象化示例 callout，请检查方法章节")
if callout_emojis.count('💡') < 2:
    print("!! WARNING: 💡 公式推导 callout 少于 2 个，请检查是否遗漏")
if callout_emojis.count('❓') == 0:
    print("!! WARNING: 没有 ❓ 读者疑问 callout，请检查实验章节")
EOF

# 1. 获取 XML 全文，统计图片和重复
lark-cli docs +fetch --api-version v2 --doc $DOC --detail full --doc-format xml --as user \
  > /tmp/lark_qc.json

python3 -c "
import json, re
from collections import Counter
with open('/tmp/lark_qc.json') as f:
    c = json.load(f)['data']['document']['content']
imgs = re.findall(r'<img[^>]+>', c)
names = [re.search(r'name=\"([^\"]+)\"', i).group(1) for i in imgs if re.search(r'name=', i)]
cnt = Counter(names)
print(f'Images: {len(imgs)}')
for nm, n in cnt.items():
    if n > 1: print(f'!! DUPLICATE: {nm}')
h3s = re.findall(r'<h3[^>]*>([^<]+)</h3>', c)
hcnt = Counter(h3s)
for h, n in hcnt.items():
    if n > 1: print(f'!! DUPLICATE H3: {h}')
print('OK' if not any(n > 1 for n in cnt.values()) else 'ISSUES FOUND')
"

# 2. 获取所有评论，检查重复
lark-cli drive file.comments list \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"is_whole\":false,\"page_size\":100}" \
  --as user > /tmp/lark_comments.json

python3 -c "
import json
from collections import Counter
with open('/tmp/lark_comments.json') as f:
    d = json.load(f)
texts = []
for c in d.get('data', {}).get('items', []):
    for r in c.get('reply_list', {}).get('replies', []):
        for e in r.get('content', {}).get('elements', []):
            t = e.get('text_run', {}).get('text', '')
            if t: texts.append(t[:60])
cnt = Counter(texts)
dups = [(t, n) for t, n in cnt.items() if n > 1]
print(f'Comments: {len(texts)}, Duplicates: {len(dups)}')
for t, n in dups:
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

## 飞书 XML 已知行为（避坑）

| 场景 | 正确做法 |
|------|----------|
| callout 内嵌代码块 | `<pre lang="python"><code>...</code></pre>` 放在 `<callout>` 内 ✅ |
| 多行代码块 | `<pre lang="..."><code>...</code></pre>`，**不要**用 `<p><code>` |
| 一次替换为多块 | `block_replace` 的 `--content` 可包含多个顶层 XML 块 ✅ |
| 图片 caption 可访问文本 | caption 在 `<img>` 属性里，`str_replace` 不会误改 |
| `str_replace` 返回结构 | result 字段在 `data.result`，不在顶层 |
| 文档内部跳转链接 | `?anchor=BLOCK_ID` 格式在**飞书 App** 内仍会打开新 Tab，**不推荐使用** |

## 错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| `images/` 目录为空 | 第一次 MinerU 结果未落地 | `ph fetch --force` 重新触发 |
| `selection-with-ellipsis` 找不到 | 文本在 callout 里已出现 | 换用更唯一的上下文文本或 `block_id` |
| comment 重复 | 相同 selection 成功两次 | `file.comments patch is_solved=true` 关闭其中一个 |
| 图片重复 | `+media-insert` 执行了两次 | `docs +update block_delete` 删除多余 block |
| `--content` JSON 报错 | shell 引号问题 | 用 `python3` 生成 JSON 再传给 subprocess |
| 占位符残留 | 忘记 Step 4 收尾 | fetch XML 找 `[图\d+位置]` block_id 后 block_delete |
