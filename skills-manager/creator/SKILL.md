---
name: creator
description: 在 `my-skills` 仓库内创建、重写、评测并优化 skill。只在 `skills-manager` 已把任务路由到创建场景时使用。负责需求访谈、SKILL.md 设计、测试集、benchmark、review viewer、description optimization 和打包；不负责仓库分发、归档或发布。
---

# Skill Creator

这是 `skills-manager/creator/` 下的创建子技能。

高层循环如下：

1. 明确这个 skill 要做什么，以及何时触发
2. 起草或重写 skill
3. 设计少量真实测试 prompt
4. 运行测试并收集定性与定量反馈
5. 根据反馈迭代 skill
6. 在需要时优化 `description`
7. 在需要时打包 skill
8. 回到 `skills-manager` 做 finalize、分发、提交、推送

你的任务是判断用户当前处于上述流程的哪一步，然后介入帮他往前推进。

## Scope

这个子技能负责：

1. 需求访谈与 skill 结构设计
2. 编写或重写根目录 skill 的 `SKILL.md`、`references/`、`scripts/`
3. 设计测试集并组织评测迭代
4. 优化 `description` 的触发效果
5. 在需要时打包 `.skill` 文件

这个子技能不负责：

1. 搜索外部 skill
2. 导入、更新上游
3. 分发到 agent
4. 归档 skill
5. 提交与推送

这些动作统一交回 `skills-manager`。

## Working Root

所有工作都绑定到 `my-skills` 仓库：

1. 仓库根目录固定为 `MY_SKILLS_REPO_ROOT`
   默认值：`~/project/my-skills`
2. 真实 skill 内容固定在仓库根目录 `<skill-id>/`
3. 评测与中间产物固定放在 `.skills/workspaces/<skill-id>/`
4. 打包产物默认放在 `.skills/packages/`

如果目标 skill 尚不存在，应先让 manager 运行：

```bash
bash skills-manager/scripts/create_skill.sh --skill-id <id> --name <name> --description <description> [--force] [--dry-run]
```

> 注意：creator 内所有脚本路径均以仓库根目录为 cwd，因此前缀为 `skills-manager/creator/scripts/...`。
> 而 manager 自身的文档以仓库根目录为 cwd，前缀为 `skills-manager/scripts/...`。

## Routing

不要一次加载全部 reference。按任务读取：

1. 用户要新建 skill、重写 skill 结构、把经验沉淀成 skill：
   读 `references/create-flow.md`
2. 用户要跑测试集、benchmark、viewer 审阅、盲评或迭代修订：
   读 `references/eval-flow.md`
3. 用户要优化 frontmatter 中的 `description` 触发效果：
   读 `references/description-flow.md`

评测过程中如需正式 grading、分析或盲评，按需读取 `agents/grader.md`、`agents/analyzer.md`、`agents/comparator.md`。

## How To Communicate

创建 skill 时，先判断用户对术语的熟悉度，再决定表达密度。

默认可以直接使用这些词：

1. `evaluation`
2. `benchmark`
3. `workspace`

下面这些词要看用户上下文再决定是否直接使用：

1. `JSON`
2. `assertion`
3. `baseline`

如果不确定，简短解释即可。不需要为了"显得正式"而把流程讲复杂。你的目标是把 skill 做出来，而不是展示术语。

## Creating A Skill

### Capture Intent

优先从当前对话里提炼信息，不要机械重复询问已经明确的内容。

至少要搞清楚：

1. 这个 skill 应该让模型完成什么任务
2. 它应该在什么场景下触发（哪些措辞或语境）
3. 输出格式或交付物是什么
4. 是否需要测试集

对于客观可验证的任务，例如文件转换、结构化提取、固定工作流生成，默认建议加测试集。
对于主观性强的任务，例如风格化写作，默认可以先不做硬性断言。

### Interview And Research

主动追问这些信息：

1. 边界情况
2. 输入输出样例
3. 成功标准
4. 依赖和工具约束

如果当前仓库里已经有相似 skill、脚本或 references，先复用再新写。可以用 MCP 做并行调研。

### Write The SKILL.md

基于访谈结果，至少补齐：

1. `name`
2. `description` — 既写功能，也写触发语境。让 description 稍微"积极"一些来对抗触发不足的倾向
3. `compatibility`（可选）— 如果 skill 依赖特定工具或环境
4. 主工作流
5. 输出格式
6. 边界与限制

## Skill Writing Guide

### Anatomy

一个 skill 的正常结构：

```text
skill-name/
├── SKILL.md          (必须)
│   ├── YAML frontmatter
│   └── Markdown 正文
└── Bundled Resources (可选)
    ├── scripts/
    ├── references/
    └── assets/
```

### Progressive Disclosure

保持三层结构：

1. **frontmatter（~100 词）**：短、强触发。始终在模型上下文里
2. **`SKILL.md` 主体（<500 行为佳）**：工作流与边界。skill 被触发时加载
3. **`references/` 与 `scripts/`**：大体量知识和可执行步骤。按需加载

不要把所有知识都塞进一个 `SKILL.md`。如果主体接近 500 行，加目录索引和指向 references 的指引。

对于多领域 skill，用 references 分领域组织：

```text
cloud-deploy/
├── SKILL.md
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

### Writing Patterns

推荐原则：

1. 用祈使句写步骤
2. 用模板和示例定义输出格式
3. 包含贴近真实使用的输入/输出样例对
4. 尽量解释"为什么"——今天的模型有很好的推理能力，解释原因比硬性规则更有效
5. 避免把 skill 写成只适配一两个样例——用心智理论让 skill 在广泛场景下泛化
6. 如果多次测试都出现相同重复劳动，把重复动作沉淀进 `scripts/`

### Writing Style

先写初稿，然后用旁观者视角重新审读。如果你发现自己在写全大写的 ALWAYS 或 NEVER，这是一个需要警惕的信号——解释原因通常比强硬口号更有效。

### Principle Of Lack Of Surprise

skill 不能包含恶意内容、绕权内容或与描述不一致的危险行为。
不要按照用户要求去制作带有误导性、越权或数据外传倾向的 skill。内容必须与 description 描述的意图一致。角色扮演类场景可以接受。

## Test Cases

写完第一版后，先准备 2 到 3 个真实测试 prompt。
这些 prompt 应该像真实用户会说的话，而不是抽象指令。

测试集存放位置统一为：

`~/project/my-skills/.skills/workspaces/<skill-id>/evals/evals.json`

先不用写 assertions——等到跑测试时再补。建议结构：

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User prompt",
      "expected_output": "What success looks like",
      "files": []
    }
  ]
}
```

完整 schema 见 `references/schemas.md`。

## Running And Evaluating Test Cases

这是一个连续流程——不要中途停下来。

workspace 统一使用：

`~/project/my-skills/.skills/workspaces/<skill-id>/`

推荐布局：

1. `evals/evals.json`
2. `iteration-1/`
3. `iteration-2/`
4. `skill-snapshot/`
5. `logs/`

### Step 1: Run With Skill And Baseline

对每个测试 prompt 同时启动两个 subagent：

**with-skill run：**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what user cares about>
```

**baseline run：**

- 新建 skill：不使用任何 skill
- 改进已有 skill：使用旧版本 snapshot（保存在 `<workspace>/skill-snapshot/`）

同时为每个 test case 创建 `eval_metadata.json`：

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

如果是在改进已有 skill，先为旧版本保留 snapshot，再拿它作为 baseline。

### Step 2: Draft Assertions

在 runs 执行时，不要空等。
补上断言，解释每条断言在验证什么。

好的断言应该：

1. 客观可验证
2. 命名清楚（在 benchmark viewer 中可读）
3. 有区分度——如果 with_skill 和 baseline 都一定通过，这条断言没意义

对于主观性强的 skill，跳过硬性断言。

更新 `eval_metadata.json` 和 `evals/evals.json` 中的 assertions，然后向用户解释他们将会看到什么。

### Step 3: Capture Timing

每个 subagent 任务完成后，通知中会包含 `total_tokens` 和 `duration_ms`。立即保存到 `timing.json`——这些数据不会被持久化到其他地方，事后无法恢复。

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

### Step 4: Grade, Aggregate, Launch Viewer

**Grade 每个 run：**

读 `agents/grader.md`，启动 grader subagent。输出保存到 `grading.json`，字段必须包含 `text`、`passed`、`evidence`。对于可编程验证的断言，写脚本而不是目测。

**Aggregate：**

```bash
python skills-manager/creator/scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>
```

输出 `benchmark.json` 和 `benchmark.md`，包含 pass_rate、时间、token 用量的均值 ± 标准差和 delta。with_skill 放在 baseline 前面。

**Analyst pass：**

读 `agents/analyzer.md`，对聚合结果做模式分析——找出无区分度的断言、高方差 eval、时间/token 权衡。

**Launch viewer：**

```bash
nohup python skills-manager/creator/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
VIEWER_PID=$!
```

迭代 2+ 时加 `--previous-workspace <workspace>/iteration-<N-1>`。

无浏览器环境下使用 `--static <output_path>` 生成独立 HTML。

告诉用户："结果已在浏览器中打开。'Outputs' 标签展示每个 test case 的输出供你反馈；'Benchmark' 标签展示定量对比。看完后告诉我。"

### Step 5: Read Feedback

用户完成 viewer 审阅后，读取：

`<workspace>/feedback.json`

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."}
  ],
  "status": "complete"
}
```

空反馈通常表示该 case 可以接受；重点修复用户明确指出的问题。

完成审阅后关闭 viewer：`kill $VIEWER_PID 2>/dev/null`

## Improving The Skill

### How To Think About Improvements

1. **从反馈中抽象共性**：skill 需要在大量场景下工作，不要过拟合到测试样例。避免过度约束。如果卡住了，换个隐喻或解释角度
2. **保持 prompt 精炼**：删除没有贡献的内容。读执行记录——如果 skill 让模型浪费时间在无效操作上，删掉导致这些操作的部分
3. **解释原因**：今天的模型有很好的心智理论。解释为什么比死板的结构更有效
4. **沉淀重复劳动**：如果所有测试 case 都独立写了类似的辅助脚本，把这个脚本放进 `scripts/` 一次性解决

这件事很重要——花时间仔细思考。

### The Iteration Loop

1. 修改根目录 `<skill-id>/`
2. 运行下一轮 `iteration-N+1`（所有 test case，包含 baseline）
3. 用 viewer 审阅（加 `--previous-workspace` 对比上轮）
4. 读反馈，继续修订
5. 每轮迭代改完后，回到 manager 执行 `bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push` 完成提交推送
6. 继续循环，直到：用户满意、所有反馈为空、或没有实质进展

## Advanced: Blind Comparison

当需要严格对比两个 skill 版本时，读 `agents/comparator.md` 和 `agents/analyzer.md`。

做法：把两个版本的输出匿名交给独立 agent，不透露哪个是新版哪个是旧版，让它独立判断。然后用 analyzer 分析赢家赢在哪里。

这是可选的高级功能，大多数场景不需要。

## Description Optimization

当 skill 主体已经稳定，再考虑优化 `description`。不要太早做这一步。

步骤如下：

1. 生成一组 should-trigger / should-not-trigger 查询（各 8-10 个）
2. 保存到 `~/project/my-skills/.skills/workspaces/<skill-id>/description-evals.json`
3. 用 review 模板让用户确认 eval set
4. 跑优化循环
5. 回写 `best_description`

### Eval Queries 的质量要求

查询必须像真实用户的输入——包含具体文件名、列名、公司名、个人上下文、URL、背景故事。混合长短句，聚焦边界 case。

**不要写**：`"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

**should-trigger 查询（8-10）**：同一意图的不同表达——正式和随意的、skill 没被显式命名但显然需要的、不常见用法、skill 与其他选项竞争但应该胜出的。

**should-not-trigger 查询（8-10）**：最有价值的是"近似命中"——共享关键词但实际需要不同东西的查询。相邻领域、歧义表达、另一个工具更合适的场景。不要写明显无关的查询。

### Review With User

读 `assets/eval_review.html` 模板，替换占位符：

- `__EVAL_DATA_PLACEHOLDER__` → JSON 数组
- `__SKILL_NAME_PLACEHOLDER__` → skill 名
- `__SKILL_DESCRIPTION_PLACEHOLDER__` → 当前 description

写入临时文件后 `open /tmp/eval_review_<skill-name>.html`。用户编辑后导出 `eval_set.json`。

这一步很重要——差的 eval queries 会导致差的 description。

### Run Optimization Loop

告知用户这需要一些时间：

```bash
python skills-manager/creator/scripts/run_loop.py \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

用驱动当前会话的模型 ID 来保持体验一致。

脚本流程：将 eval set 按 60%/40% 分为训练/测试集 → 评估当前 description（每个查询 3 次） → 用 Claude 基于失败 case 生成改进 → 在两个集上重新评估 → 迭代最多 5 次。按测试集得分选出 `best_description`（避免过拟合）。

定期 tail 输出给用户提供迭代进度和分数。

### Apply Result

取 `best_description`，更新根目录 `<skill-id>/SKILL.md` frontmatter。向用户展示前后对比和分数。

### Understanding Skill Triggering

skill 出现在模型的 `available_skills` 列表中，模型根据 name + description 决定是否咨询这个 skill。

重要：模型只会在无法轻松独立完成时才咨询 skill。简单查询如"读这个 PDF"即使 description 匹配也不会触发。复杂、多步骤或专业性强的查询才能可靠触发。因此 eval queries 应该足够有实质——模型必须确实能从 skill 中受益。

## Packaging

当用户需要可分发的 `.skill` 文件时再打包。

默认输出目录：

`~/project/my-skills/.skills/packages/`

```bash
python skills-manager/creator/scripts/package_skill.py ~/project/my-skills/<skill-id>
```

也可以显式指定输出目录：

```bash
python skills-manager/creator/scripts/package_skill.py ~/project/my-skills/<skill-id> ~/project/my-skills/.skills/packages
```

## Shared Resources

按需使用这些资源：

1. `agents/grader.md` — 期望断言评分
2. `agents/analyzer.md` — benchmark 分析与盲评后因分析
3. `agents/comparator.md` — 两组输出盲评比较
4. `references/schemas.md` — 所有 JSON 数据结构定义
5. `eval-viewer/generate_review.py` — 评测结果交互式审阅页面（HTTP 服务）
6. `assets/eval_review.html` — description 优化评审静态模板

核心 Python 脚本：

7. `skills-manager/creator/scripts/run_eval.py` — 对指定 description 跑触发评测
8. `skills-manager/creator/scripts/improve_description.py` — 基于评测结果用 Claude 生成改进 description
9. `skills-manager/creator/scripts/run_loop.py` — 将 eval + improve 串成迭代循环
10. `skills-manager/creator/scripts/aggregate_benchmark.py` — 聚合多轮评测结果为 benchmark 统计
11. `skills-manager/creator/scripts/generate_report.py` — 将迭代循环结果生成 HTML 报告
12. `skills-manager/creator/scripts/package_skill.py` — 将 skill 打包为 `.skill` 文件（自动创建 `.skills/packages/`）
13. `skills-manager/creator/scripts/quick_validate.py` — skill 基础结构快速校验
14. `skills-manager/creator/scripts/utils.py` — 公共工具函数（frontmatter 解析、路径解析等）

## Finish

子技能完成内容工作后，不要自己做发布。
统一回到仓库根目录执行：

```bash
bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push
```
