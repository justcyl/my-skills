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
Step 1.5  建立术语表                    ← 扫描 full.md，分类术语，写入 glossary.md
     │   A类（有共识）直接译，B类（专有）用「中文（英文）」格式
     ▼
Step 2  翻译正文                        ← 中文翻译，写入 /tmp/<arxiv_id>_zh.md
     │   全文遵循术语表，同一术语只有一种译法
     │   分多次写入避免工具超限
     ▼
Step 2.5  启动段落摘要子代理（异步）    ← herdr pane_split，gpt-5.4 处理语义载荷段落
     │   与 Step 3/4 并行，Step 5 前同步
     ▼
Step 3  lark-cli docs +create          ← 在飞书个人文档库创建文档（默认 my_library）
     │   ⚠️ 文档标题由 --title 参数设定，不是正文里的 # 一级标题
     │
     ▼
Step 3-meta  写入论文元信息块             ← 在文档最前端插入原文地址/创建时间/元数据 callout
     │
     ▼
Step 3.5  公式渲染替换                  ← 扫描 $$...$$ / $...$ → <equation> XML 块
     │   详见 references/formulas.md
     ▼
Step 4  插入图片 + 删除占位符           ← 逐张 docs +media-insert
     │   插入后 block_delete 占位符块
     ▼
Step 5  添加注释层                      ← 详见 references/annotate.md
     │   callout（公式推导/具象化/引用/疑问/代码）
     │   comment（术语/段落摘要，段落摘要由子代理预计算）
     ▼
Step 5.5  代码仓库集成（可选）          ← 论文有开源代码时执行
     │   克隆仓库 → 阅读核心模块 → 以 callout 内嵌代码块注入文档
     ▼
Step 6  展开关键参考文献                ← ph fetch 被引论文，inline callout
     │
     ▼
Step 7  质量检查                        ← 详见 references/qc.md
     │   检测重复图片/评论/callout
     ▼
Step 8  视觉验证（必须）                ← 导出 PDF → pdftoppm 转图 → 视觉模型逐页审查
         发现公式未渲染、XML 裸标签、排版异常等脚本检测不到的问题
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

## Step 1.5：建立术语表

**翻译开始前必须先完成此步骤**，确保全文术语一致。

### 扫描步骤

读取 `full.md`，提取所有：
- 论文自创的方法名/模块名（如 Evolving Parameter Isolation、Skill Library）
- 无固定中文译名的新兴概念（如 agent swarm、continual pre-training）
- 论文中反复出现的缩写（EPI、PEFT、SFT、LoRA 等）
- 数据集和模型名（通常保留英文，确认即可）

### 术语分类规则

| 类别 | 判断标准 | 翻译格式 |
|------|---------|---------|
| **A类（有共识）** | 中文学界已有约定译名（如"注意力机制"、"灾难性遗忘"、"微调"） | 直接使用中文，不注英文 |
| **B类（论文专有/无共识）** | 作者自创术语，或中文有多种译法且未形成共识 | 首次出现用「**中文（英文全称）**」，后续只写中文 |
| **C类（保留英文）** | 专有名词、模型名、数据集名（GPT-4、MMLU、LoRA） | 直接使用英文，不强行翻译 |

### 输出格式

写入 `/tmp/<arxiv_id>_glossary.md`：

```markdown
# 术语表 | <论文标题>

## A类：有共识，直接译（不注原文）
| 英文 | 中文译名 |
|------|---------|
| catastrophic forgetting | 灾难性遗忘 |
| fine-tuning | 微调 |
| attention mechanism | 注意力机制 |

## B类：无共识/论文专有（首次出现格式：中文（英文全称））
| 英文 | 中文译名 | 首次出现格式 |
|------|---------|-------------|
| Evolving Parameter Isolation | 演化参数隔离 | 演化参数隔离（Evolving Parameter Isolation，EPI） |
| skill library | 技能库 | 技能库（skill library） |
| agent swarm | 代理群 | 代理群（agent swarm） |

## C类：保留英文
- GPT-4、LLaMA-3、LoRA、DoRA、MMLU、HellaSwag
```

> **B类首次出现后**：后续段落只写中文译名，不重复注英文。缩写（EPI）在首次展开后可单独使用。

---

## Step 2：翻译

逐节翻译，保留：
- 所有公式（原样保留 LaTeX，不翻译符号）
- 图表位置标记（`[图X位置]` 占位，稍后由 Step 4 替换为实际图片）
- 节标题层级

翻译原则：
- **严格遵循术语表**（Step 1.5 生成的 `/tmp/<arxiv_id>_glossary.md`）：同一术语全文只使用一种译法，不可一处用 A 一处用 B
- **B类术语格式**：首次出现用「中文（英文全称，缩写）」完整格式，后续只写中文
- **A类术语**：直接使用中文，不需要注英文
- **C类（专有名词/模型名）**：保留英文，不强行翻译
- 不压缩信息，逐节完整翻译
- 附录完整翻译在末尾，不做前置处理
- **公式必须保留 LaTeX 原文**：独立公式写为独立行 `$$...$$`（前后空行），行内公式写为 `$...$`。**严禁**将 LaTeX 转为 Unicode 符号（如把 `$\sum$` 写成 `∑`，把 `$\pi_	heta$` 写成 `π_θ`）——Unicode 符号无法被 Step 3.5 识别，公式将永久以纯文字形式残留在文档里

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

## Step 2.5：启动段落摘要子代理（异步）

翻译写入完毕后，**立即**在后台 pane 启动子代理处理长段落摘要。子代理与主流程的 Step 3、4 并行运行，Step 5 前同步结果。

### 异步启动

用 herdr 工具依次执行：

```json
{ "action": "pane_split", "pane": "current", "direction": "down", "newPane": "para-summarizer" }
```

```json
{
  "action": "run",
  "pane": "para-summarizer",
  "command": "pi --print --model axonhub/gpt-5.4 --thinking off --tools read,bash --system-prompt ~/.agents/skills/lark-paper-reader/agents/paragraph-summarizer.prompt.md --no-skills --no-context-files --no-extensions --no-session 'ZH_MD=/tmp/<arxiv_id>_zh.md OUTPUT=/tmp/<arxiv_id>_summaries.json'"
}
```

**不等待**，立即继续执行 Step 3。

> 子代理定义详见 [`agents/paragraph-summarizer.md`](agents/paragraph-summarizer.md)。

---

## Step 3：创建飞书文档

统一存放在固定文件夹（`PAPER_FOLDER_TOKEN`）：

> **标题设置警告：** 飞书文档的标题由 `--title` 参数设定，**不是** Markdown 正文里的 `# 一级标题`。zh.md 里的一级标题上传后展示为正文第一个条目，不会自动变成标题栏。请始终通过 `--title` 传入题目。

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

> `--api-version v2` **仅在 `docs +create` 时需要**（启用 Markdown 建文档）。其他所有命令（fetch、update、block 操作）使用默认 v1，不要加此 flag，否则可能触发 EOF 错误。

---

## Step 3-meta：写入论文元信息块

文档创建完成后，立即在文档最前端（封面标题块之后）插入一个包含论文元信息的 callout。这是读者进入文档第一眼看到的路标。

```bash
DOC=<document_id>
ARXIV_ID=<arxiv_id>  # 例: 2604.24827

# 获取论文元数据（已在 Step 1 import 时入库）
META=$(uv run --project ~/project/ph2 ph fetch \
  --paper-id arxiv://$ARXIV_ID 2>&1)

TITLE=$(echo "$META" | python3 -c \
  'import json,sys; d=json.load(sys.stdin); print(d["result"][0]["title"])')
AUTHORS=$(echo "$META" | python3 -c \
  'import json,sys; d=json.load(sys.stdin); print(d["result"][0]["authors"])')
YEAR=$(echo "$META" | python3 -c \
  'import json,sys; d=json.load(sys.stdin); print(d["result"][0].get("year",""))')

# 当前时间（精确到分钟）
CREATED=$(date '+%Y-%m-%d %H:%M')
```

然后用 `block_insert_after` 将元信息 callout 插入到封面标题块之后：

```bash
# 先 fetch XML 找到标题块 id
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user \
  > /tmp/lark_meta_tmp.json

TITLE_BLOCK=$(python3 -c "
import json, re
with open('/tmp/lark_meta_tmp.json') as f:
    c = json.load(f)['data']['document']['content']
# 飞书文档第一个块通常是 page title´
first = re.search(r'<page[^>]*id=\"(doxcn[^\"]+)\"', c)
if first: print(first.group(1))
else:
    # 退而求其次：找文档第一个 h1
    h1 = re.search(r'<h1[^>]*id=\"(doxcn[^\"]+)\"', c)
    if h1: print(h1.group(1))
")

lark-cli docs +update --doc "$DOC" \
  --command block_insert_after \
  --block-id "$TITLE_BLOCK" \
  --content "<callout emoji=\"📄\" background-color=\"light-gray\" border-color=\"gray\">
<p><b>论文标题</b>：$TITLE</p>
<p><b>作者</b>：$AUTHORS</p>
<p><b>年份</b>：$YEAR</p>
<p><b>原文地址</b>：https://arxiv.org/abs/$ARXIV_ID</p>
<p><b>论文 PDF</b>：https://arxiv.org/pdf/$ARXIV_ID</p>
<p><b>本文档创建时间</b>：$CREATED</p>
</callout>" \
  --doc-format xml \
  --as user
```

> **注意**：若飞书文档没有 `<page>` 块，就用文档第一个 h1 块的 block-id 作为插入点。元信息 callout 应位于导读 callout（Step 5a）之前。

---

## Step 3.5：公式渲染替换

飞书 markdown 上传**不渲染 LaTeX**——`$$...$$` 和 `$...$` 以字面字符串写入文档。本步骤将它们替换为飞书原生 `<equation>` XML 块。

详细语法和完整脚本见 [references/formulas.md](references/formulas.md)。

```bash
DOC=<document_id>

# 先 fetch 最新 XML
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user   > /tmp/lark_formula_pass.json

# 运行公式替换（独立公式 + 行内公式）
python3 ~/.agents/skills/lark-paper-reader/references/formulas.md
# ↑ 实际执行时把脚本内容粘贴到 python3 -c 或单独 .py 文件中运行
```

> 如果 zh.md 里公式已被写成 Unicode（`∑`、`π_θ` 等），本步骤无法恢复——需回到 Step 2 重新翻译该部分，保留 LaTeX 格式后重建文档。

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
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user \
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
lark-cli docs +update --doc "$DOC" \
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
lark-cli docs +fetch --doc "$DOC" --detail full --doc-format xml --as user \
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

# 长段落（>80字，参考用——段落摘要已由子代理批量处理）
long_ps = re.findall(r'<p[^>]*id="(doxcn[^"]+)"[^>]*>(.{80,}?)</p>', content, re.DOTALL)
print(f"\n=== 长段落: {len(long_ps)} 个 ===")
for bid, text in long_ps[:5]:
    print(f"  [{bid}] {text[:50].strip()}...")
print(f"  (共 {len(long_ps)} 个，段落摘要由子代理预计算；此处确认覆盖情况)")
EOF
```

把章节列表逐条检查 callout 覆盖情况，**处理完一个在列表里划掉一个**，不允许凭印象跳过。

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
| ❓ | 读者常见疑问 | 语义密度高、读者可能困惑、作者有言外之意的任意位置（不限于实验节） |

**🔧 类型的 callout 可以内嵌代码块**，将说明和代码封装在同一视觉容器（具体语法见 Step 5.5 § 3）。

`block_replace` 支持一次替换为多个顶层块，可用来把「旧 callout」替换为「新 callout + 独立 pre 块」，或直接替换为「含 pre 的 callout」：

```bash
# 将 OLD_CALLOUT_ID 替换为：新 callout（含嵌入代码块）
lark-cli docs +update --doc "$DOC" \
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

**Step 5 开始前：等待子代理完成**（Step 2.5 启动的 `para-summarizer` pane）：

```json
{ "action": "wait_agent", "pane": "para-summarizer", "statuses": ["done", "idle"], "timeout": 300000 }
```

检查子代理输出：

```bash
if [ -f /tmp/<arxiv_id>_summaries.json ]; then
  python3 -c "import json; d=json.load(open('/tmp/<arxiv_id>_summaries.json')); print(f'子代理完成，共 {len(d)} 条段落摘要')"
else
  echo '子代理未产出结果，将手动处理段落摘要'
fi
```

#### 段落摘要（优先使用子代理预计算结果）

```python
import subprocess, json

DOC = "<document_id>"
summaries_path = "/tmp/<arxiv_id>_summaries.json"

with open(summaries_path) as f:
    summaries = json.load(f)

for item in summaries:
    content_json = json.dumps(
        [{"type": "text", "text": item["comment"]}],
        ensure_ascii=False
    )
    result = subprocess.run(
        ["lark-cli", "drive", "+add-comment",
         "--doc", DOC, "--type", "docx",
         "--selection-with-ellipsis", item["para_start"],
         "--content", content_json, "--as", "user"],
        capture_output=True, text=True
    )
    status = "✓" if result.returncode == 0 else "✗"
    print(f"{status} {item['para_start'][:30]}")
```

如果子代理未产出结果（JSON 不存在或为空），回退到手动逐段添加。

#### 术语注释（手动处理，子代理不负责）

```python
content_json = json.dumps([{"type": "text", "text": "注释内容"}], ensure_ascii=False)
subprocess.run(["lark-cli", "drive", "+add-comment",
    "--doc", DOC, "--type", "docx",
    "--selection-with-ellipsis", "<唯一定位文本>",
    "--content", content_json, "--as", "user"])
```

触发时机：每个专业术语第一次出现时 → 简短定义（1-2 句）

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
lark-cli docs +fetch --doc $DOC --detail full --doc-format xml --as user \
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
print(f"长段落数(参考，段落摘要由子代理预计算): {len(long_paras)}")

if callout_emojis.count('🌉') == 0:
    print("!! WARNING: 没有任何 🌉 具象化示例 callout，请检查方法章节")
if callout_emojis.count('💡') < 2:
    print("!! WARNING: 💡 公式推导 callout 少于 2 个，请检查是否遗漏")
if callout_emojis.count('❓') == 0:
    print("!! WARNING: 没有 ❓ 读者疑问 callout，请检查全文（方法/实验/分析均可触发）")
EOF

# 1. 获取 XML 全文，统计图片和重复
lark-cli docs +fetch --doc $DOC --detail full --doc-format xml --as user \
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
lark-cli docs +update --doc $DOC \
  --command block_delete --block-id <dup_block_id> --as user

# 将重复评论标记为 resolved
lark-cli drive file.comments patch \
  --params "{\"file_token\":\"$DOC\",\"file_type\":\"docx\",\"comment_id\":\"<id>\"}" \
  --data '{"is_solved":true}' --as user
```

---

## Step 8：视觉验证（必须）

Step 7 的脚本检查只能发现 XML 层面的结构问题（重复 block、占位符残留等）。**视觉验证**通过视觉模型逐页阅读 PDF，能发现脚本盲区：公式渲染失败、callout 内 `$...$` 未渲染、XML 标签裸露、图片缺失/乱序、字符转义异常等。**本步骤为必须步骤，不可跳过。**

### 8-1. 导出 PDF

```bash
DOC=<document_id>

# 导出（在目标目录执行，lark-cli 要求相对路径）
cd /tmp && lark-cli drive +export \
  --token "$DOC" \
  --doc-type docx \
  --file-extension pdf \
  --output-dir . \
  --overwrite \
  --as user
# 若提示 unsafe path，先确认 cd 到了目标目录
```

若 export 因路径问题失败并返回 `file_token`，用 `+export-download` 单独下载：

```bash
cd /tmp && lark-cli drive +export-download \
  --file-token "<export_file_token>" \
  --file-name "output.pdf" \
  --output-dir "." \
  --overwrite --as user
```

### 8-2. PDF 转图片

```bash
PDF_PATH="/tmp/output.pdf"
OUT_DIR="/tmp/doc_pages"
mkdir -p "$OUT_DIR"

# 用 pdftoppm（推荐，poppler-utils）
pdftoppm -r 150 -png "$PDF_PATH" "$OUT_DIR/page"

# 或用 pymupdf（Python）
# python3 -c "import fitz; doc=fitz.open('$PDF_PATH'); [doc[i].get_pixmap(dpi=150).save('$OUT_DIR/page-%02d.png'%(i+1)) for i in range(len(doc))]"

ls "$OUT_DIR/" | wc -l   # 确认页数
```

### 8-3. 视觉模型逐页审查

在 herdr 子 pane 中调用视觉模型（支持图片的模型，如 `gemini-3.1-pro-preview`）：

```json
{ "action": "pane_split", "pane": "current", "direction": "down", "newPane": "doc-reviewer" }
```

```json
{
  "action": "run",
  "pane": "doc-reviewer",
  "command": "pi --print --model axonhub/gemini-3.1-pro-preview --thinking off --tools read,bash --no-skills --no-context-files --no-extensions --no-session '你是飞书文档质检员。请逐页阅读 /tmp/doc_pages/ 下的所有 PNG，检查以下问题并输出报告：1.公式渲染：是否有「无效公式」红色标记、或公式显示为 LaTeX 字符串（如 \\mathcal{J}）2.图片：是否正常显示、是否有乱序或缺失 3.Callout：📍💡🌉❓📖🔧 是否正常渲染为彩色方块 4.排版：段落间距、标题层级是否正常 5.其他视觉异常：乱码、重复内容、XML 标签裸露等。每页一行简短描述，最后给出需要修复的问题列表（优先级：高/中/低）。'"
}
```

等待子代理完成：

```json
{ "action": "wait_agent", "pane": "doc-reviewer", "statuses": ["done", "idle"], "timeout": 300000 }
```

然后读取报告：

```json
{ "action": "read", "pane": "doc-reviewer", "lines": 100, "source": "recent-unwrapped" }
```

### 8-4. 常见视觉问题修复

**公式渲染失败（「无效公式」红标）**

通常是 `<latex>` 块内含双重转义的 HTML 实体（`&amp;lt;` 应为 `&lt;`）：

```python
# fetch XML → 找所有 <latex> 内含 &amp;lt;/&amp;gt; 的块 → 修复
import json, re, subprocess, html as html_mod

DOC = "<document_id>"
with open('/tmp/lark_qc.json') as f:
    c = json.load(f)['data']['document']['content']

for m in re.finditer(r'<p[^>]*id="(doxcn[^"]+)"[^>]*>(.*?)</p>', c, re.DOTALL):
    bid, inner = m.group(1), m.group(2)
    if '&amp;lt;' not in inner and '&amp;gt;' not in inner:
        continue
    def fix_latex(lm):
        return '<latex>' + lm.group(1).replace('&amp;lt;','&lt;').replace('&amp;gt;','&gt;') + '</latex>'
    fixed = re.sub(r'<latex>(.*?)</latex>', fix_latex, inner, flags=re.DOTALL)
    subprocess.run(['lark-cli','docs','+update','--doc',DOC,
        '--command','block_replace','--block-id',bid,
        '--content',f'<p>{fixed}</p>','--doc-format','xml','--as','user'],
        capture_output=True)
    print(f'✓ fixed [{bid}]')
```

**Callout 内公式显示为字符串（`$...$` 未渲染）**

Callout XML 内的公式必须用 `<latex>` 标签，不能用 `$...$`。修复：

```python
# 找所有含 $...$ 的段落（在 callout 内）→ 转为 <latex> 标签
for m in re.finditer(r'<p[^>]*id="(doxcn[^"]+)"[^>]*>(.*?)</p>', c, re.DOTALL):
    bid, inner = m.group(1), m.group(2)
    if '$' not in inner:
        continue
    # 按 XML 标签拆分，只对纯文字部分做替换
    parts = re.split(r'(<[^>]+>)', inner)
    new_inner = ''
    for part in parts:
        if part.startswith('<'):
            new_inner += part
        else:
            new_inner += re.sub(r'\$([^$<]+?)\$',
                lambda lm: f'<latex>{html_mod.escape(lm.group(1))}</latex>', part)
    if new_inner != inner:
        subprocess.run(['lark-cli','docs','+update','--doc',DOC,
            '--command','block_replace','--block-id',bid,
            '--content',f'<p>{new_inner}</p>','--doc-format','xml','--as','user'],
            capture_output=True)
        print(f'✓ fixed $ [{bid}]')
```

**XML 标签裸露（`<text>`、`</equation>` 出现在文档正文中）**

原因：`block_replace` 时提交了 `<p><text>...</text><equation>...</equation></p>` 格式，lark-cli 不识别 `<text>` 子元素，把 XML 当字面字符串写入。修复：找出含 `&lt;text&gt;` 的段落，解码后用 `<latex>` 重建：

```python
broken = re.findall(r'id="(doxcn[^"]+)"[^>]*>((?:[^<]|<(?!/?p[> ]))*&lt;(?:text|equation)[^<]*)', c, re.DOTALL)
for bid, raw in broken:
    decoded = html_mod.unescape(raw)
    # <text>X</text> → X，<equation inline="true">X</equation> → <latex>X</latex>
    fixed = re.sub(r'</?text[^>]*>', '', decoded)
    fixed = re.sub(r'<equation\s+inline="true">(.*?)</equation>',
        lambda lm: f'<latex>{html_mod.escape(lm.group(1))}</latex>', fixed, flags=re.DOTALL)
    subprocess.run(['lark-cli','docs','+update','--doc',DOC,
        '--command','block_replace','--block-id',bid,
        '--content',f'<p>{fixed}</p>','--doc-format','xml','--as','user'],
        capture_output=True)
    print(f'✓ fixed bare-tag [{bid}]')
```

---

## 前置配置（由各 skill 负责）

- **飞书认证 & 文件夹**：由 [`lark`](../lark/SKILL.md) 管理。确认已 `lark-cli auth status`。Step 3 默认使用 `--parent-position my_library`；如需指定文件夹，通过飞书网页 URL `/drive/folder/<token>` 获取 token，替换 `--parent-position` 为 `--parent-token <token>`。
- **MinerU token（`PH_MINERU_TOKEN`）**：由 [`ph-paper-helper`](../ph-paper-helper/SKILL.md) 管理。未配置时 `ph fetch` 无法解析 PDF 图片，降级为纯文本模式。

---

## 飞书 XML 已知行为（避坑）

| 场景 | 正确做法 |
|------|----------|
| 独立公式块 | `<equation>LaTeX</equation>` 顶层块 ✅ |
| 行内公式（lark-cli 写入时） | `<p>文字<latex>LaTeX</latex>文字</p>`，**直接用 `<latex>` 标签** ✅ |
| 行内公式（飞书 XML 返回格式） | `<p>文字<latex>LaTeX</latex>文字</p>`，读取与写入格式一致 |
| lark-cli 上传 markdown 的公式 | `$...$` 和 `$$...$$` 会被**自动转为 `<latex>` 标签**，无需手动转换 |
| callout 内的公式 | 必须用 `<latex>LaTeX</latex>`，**不能用 `$...$`**（markdown 公式在 callout XML 里不渲染） |
| `<p>` 内的 `<text>` 子元素 | `block_replace` 时**不要**在 `<p>` 内加 `<text>` 包裹——lark-cli 不识别此结构，会把整段 XML 当字面字符串写入 |
| LaTeX 中含 `<` `>` `&` | 在 XML 中用 `&lt;` `&gt;` `&amp;` 转义一次；**不要** `html.escape()` 已经转义的内容（否则 `&lt;` → `&amp;lt;` 双重转义，渲染失败） |
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
| 公式「无效公式」红标 | `<latex>` 内含 `&amp;lt;` 双重转义 | 见 Step 8-4 修复脚本 |
| Callout 公式显示为 `$...$` 字符串 | callout XML 内误用 markdown `$` 语法 | 见 Step 8-4 修复脚本 |
| XML 标签（`<text>`）裸露在正文 | `block_replace` 时提交了含 `<text>` 子元素的 `<p>` | 见 Step 8-4 修复脚本 |
| `drive +export` 报 unsafe path | lark-cli 要求相对路径 | 先 `cd` 到目标目录再执行 |
