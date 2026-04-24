# OpenReview 审稿意见抓取与解读

## 核心视角

OpenReview 的公开审稿是读论文时最被忽视的金矿。
reviewer 的批评往往比论文正文更诚实，能让你快速看到：
- 这篇论文真正的弱点在哪里
- 作者是怎么辩护的（rebuttal）
- 审稿人最终有没有被说服

这对写自己的论文帮助极大——你知道了什么样的弱点会被抓住，什么样的回复能让评分提升。

---

## Step 1：找到 OpenReview 页面

**方式一：直接搜索**
```
https://openreview.net/search?term=<论文标题关键词>
```

**方式二：arXiv 页面找链接**
很多论文在 arXiv 的 Comments 字段会标注 OpenReview 链接。

**方式三：构造 URL（如果知道 paper ID）**
```
https://openreview.net/forum?id=<PAPER_ID>
```

**哪些论文有 OpenReview？**
主要是走 OpenReview 系统的会议：ICLR（最完整）、NeurIPS（近年）、ICML（近年）、部分 workshop。
ACL/EMNLP 系列目前使用 ARR 系统，审稿不公开。

---

## Step 2：抓取 OpenReview 内容

### 使用 web-reader skill 抓取

如果当前环境有 `web-reader` skill，用它读取 OpenReview 页面：

```
请用 web-reader 读取以下页面：
https://openreview.net/forum?id=<PAPER_ID>
```

### 使用 OpenReview API 直接获取结构化数据

OpenReview 提供公开 API，返回 JSON 格式的完整审稿信息：

```bash
# 获取论文的所有 notes（包含 reviews、rebuttal、meta-review）
curl "https://api2.openreview.net/notes?forum=<PAPER_ID>&details=replyCount" \
  | python3 -m json.tool
```

或者用 Python 获取更干净的结果：

```python
import requests, json

paper_id = "<PAPER_ID>"  # 替换为实际 ID
url = f"https://api2.openreview.net/notes?forum={paper_id}"
resp = requests.get(url)
notes = resp.json()["notes"]

for note in notes:
    invitation = note.get("invitation", "")
    content = note.get("content", {})
    
    # 过滤出 review 类型的 note
    if "Official_Review" in invitation or "Review" in invitation:
        rating = content.get("rating", content.get("recommendation", "N/A"))
        confidence = content.get("confidence", "N/A")
        summary = content.get("summary", "")[:200]
        print(f"Rating: {rating} | Confidence: {confidence}")
        print(f"Summary: {summary}\n")
```

---

## Step 3：解读审稿结构

### ICLR 评分体系

| 分数 | 含义 |
|---|---|
| 10 | Strong Accept（顶级，极少） |
| 8 | Accept |
| 6 | Weak Accept（borderline 偏好） |
| 5 | Borderline（最常见的争议区） |
| 3 | Weak Reject |
| 1 | Strong Reject |

**Confidence 分**（1-5）：reviewer 对领域的熟悉程度，5 表示非常熟悉。
低 confidence + 低分 → 可能是不熟悉领域的误判，值得在 rebuttal 中澄清。

### 审稿意见的典型结构

一份好的 review 通常包含：
1. **Summary**：reviewer 对论文的理解（可以看看他理解对了没有）
2. **Strengths**：认可的地方
3. **Weaknesses**：核心批评
4. **Questions**：需要作者回复的问题
5. **Rating + Confidence**

---

## Step 4：重点阅读内容

读审稿时，关注这几个维度：

### 1. Weaknesses 的模式

把所有 reviewer 的 Weakness 汇总，找共性：

| 批评类型 | 含义 | 写作启示 |
|---|---|---|
| "The comparison is unfair" | Baseline 选择有问题 | 实验设计要全面，baseline 要新 |
| "Missing ablation on X" | 某个设计没有被单独验证 | 提前做好每个模块的消融 |
| "The contribution is incremental" | 认为方法只是小改 | 引言要把 novelty 写得更清晰 |
| "The writing is unclear" | 表达有问题 | 重点检查方法节和引言 |
| "Limited generalizability" | 只在特定场景有效 | 要么做更多实验，要么在 limitation 里承认 |
| "Missing related work: X" | 漏了某篇重要论文 | 相关工作要覆盖全 |

### 2. Rebuttal 质量

看作者怎么回复 reviewer：

- **好的 rebuttal**：直接承认问题，给出额外实验或数据；或者清晰指出 reviewer 理解有误
- **差的 rebuttal**：避重就轻，没有实质新信息，只是重复论文里已有的内容

rebuttal 之后 reviewer 有没有改分？这是衡量 rebuttal 是否有效的最直接指标。

### 3. 最终决策

- **Meta-review**：AC（Area Chair）的最终决策意见，会综合所有 reviewer 的意见
- 如果论文被拒，meta-review 通常会说清楚主要拒稿原因

---

## Step 5：审稿辅助解读

当获取到审稿内容后，按以下维度帮用户整理：

### 输出格式

```
## OpenReview 审稿摘要

**会议**：ICLR 2024  
**决定**：Accepted（Poster）/ Rejected  
**评分分布**：[8, 6, 5, 6]（均值 6.25）

---

### Reviewer 1（Rating: 8, Confidence: 4）
**主要认可**：...
**主要质疑**：...
**关键问题**：...

### Reviewer 2（Rating: 5, Confidence: 3）
**主要认可**：...
**主要质疑**：...
**关键问题**：...

---

### 共性批评（多个 Reviewer 都提到）
1. ...
2. ...

### Author Rebuttal 策略
- 对问题 X，作者提供了额外实验 → Reviewer 1 评分从 5 → 6
- 对问题 Y，作者澄清了误解 → 未改分

### 对写论文的启示
1. [从这次审稿里学到的写作/实验建议]
2. ...
```

---

## 分析 Checklist

- [ ] 找到了 OpenReview 页面？（用 forum ID 确认）
- [ ] 记录了每位 reviewer 的评分和 confidence？
- [ ] 汇总了所有 reviewer 的共性批评？
- [ ] 分析了 rebuttal 是否有效（评分是否改变）？
- [ ] 提炼了对自己写论文有用的启示？
