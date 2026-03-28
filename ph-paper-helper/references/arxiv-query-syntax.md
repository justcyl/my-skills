# arXiv 查询语法参考

`ph search --query` 的值直接传给 arXiv API 的 `search_query` 参数。掌握以下语法可以显著提升搜索精度。

## 字段限定符

| 前缀 | 含义 | 示例 |
|------|------|------|
| `ti:` | 标题 | `ti:transformer` |
| `au:` | 作者 | `au:vaswani` |
| `abs:` | 摘要 | `abs:self-attention` |
| `cat:` | arXiv 类别 | `cat:cs.CV` |
| `all:` | 所有字段 | `all:diffusion` |

不加前缀等同于 `all:`。

## 布尔运算

| 运算 | 语法 | 示例 |
|------|------|------|
| 与 | `AND` | `ti:diffusion AND cat:cs.CV` |
| 或 | `OR` | `ti:transformer OR ti:attention` |
| 非 | `ANDNOT` | `ti:diffusion ANDNOT ti:image` |

布尔运算符必须大写。

## 分组

用括号分组：

```
ti:(transformer OR attention) AND cat:cs.CL
```

## 常用 arXiv 类别

AI/ML 相关的常见类别：

| 类别 | 领域 |
|------|------|
| `cs.AI` | 人工智能 |
| `cs.CL` | 计算语言学（NLP） |
| `cs.CV` | 计算机视觉 |
| `cs.LG` | 机器学习 |
| `cs.RO` | 机器人学 |
| `cs.IR` | 信息检索 |
| `cs.NE` | 神经与进化计算 |
| `stat.ML` | 统计机器学习 |
| `eess.IV` | 图像与视频处理 |
| `cs.CR` | 密码学与安全 |
| `cs.SE` | 软件工程 |
| `cs.DC` | 分布式计算 |
| `cs.DB` | 数据库 |

## 查询构造策略

### 主题搜索

核心原则：**少即是多**。arXiv 搜索不支持语义理解，关键词太多会漏掉结果。

```bash
# ✓ 好：2-3 个核心术语
ph search --query "ti:diffusion AND ti:video" --max-results 15

# ✗ 差：过多限定
ph search --query "ti:diffusion AND ti:video AND ti:generation AND ti:temporal AND ti:consistency"
```

### 处理同义词

用 OR 覆盖不同表达：

```bash
ph search --query "ti:(LLM OR large language model) AND abs:reasoning"
```

### 结合类别限定

当领域明确时，加 `cat:` 可以大幅减少噪声：

```bash
# 只看 NLP 方向的 retrieval augmented generation
ph search --query "abs:retrieval augmented generation AND cat:cs.CL" --max-results 15
```

### 作者搜索

```bash
# 某作者的所有论文
ph search --query "au:hinton" --sort-by submittedDate --sort-order desc --max-results 20

# 某作者在特定主题的工作
ph search --query "au:song AND ti:diffusion" --max-results 10
```

### 找最新工作

```bash
ph search --query "ti:reasoning AND cat:cs.CL" --sort-by submittedDate --sort-order desc --max-results 20
```

### 搜索结果不理想时的调整策略

1. **结果太少**：
   - 减少限定词（去掉 `cat:`、把 `ti:` 换成 `abs:` 或 `all:`）
   - 用 OR 增加同义词
   - 增大 `--max-results`

2. **结果不相关**：
   - 加 `cat:` 限定领域
   - 把 `all:` 换成 `ti:` 或 `abs:` 提高精度
   - 换更具体的术语

3. **找特定论文找不到**：
   - 用标题中最独特的 2-3 个词做 `ti:` 搜索
   - 如果知道 arXiv ID，直接用 `ph add --input arxiv://ID`
