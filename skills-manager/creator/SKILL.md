---
name: skill-creator
description: 在 `my-skills` 仓库内创建、重写、评测并优化 skill。只在 `skills-manager` 已把任务路由到创建场景时使用。负责需求访谈、SKILL.md 设计、测试集、benchmark、review viewer、description optimization 和打包；不负责仓库分发、归档或发布。
---

# Skill Creator

这是 `skills-manager/creator/` 下的创建子技能，不是独立总控。

高层循环如下：

1. 明确这个 skill 要做什么，以及何时触发
2. 起草或重写 skill
3. 设计少量真实测试 prompt
4. 运行测试并收集定性与定量反馈
5. 根据反馈迭代 skill
6. 在需要时优化 `description`
7. 在需要时打包 skill
8. 回到 `skills-manager` 做 finalize、分发、提交、推送

你的职责不是重新实现一套仓库治理逻辑，而是把 skill 本身做对、做稳、做清楚。

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

> 注意：creator 内所有脚本路径均以仓库根目录为 cwd，因此前缀为 `skills-manager/scripts/...`。
> 而 manager 自身的文档以 `skills-manager/` 为 cwd，前缀为 `scripts/...`。

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

不需要为了“显得正式”而把流程讲复杂。你的目标是把 skill 做出来，而不是展示术语。

## Creating A Skill

### Capture Intent

优先从当前对话里提炼信息，不要机械重复询问已经明确的内容。

至少要搞清楚：

1. 这个 skill 应该让模型完成什么任务
2. 它应该在什么场景下触发
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

如果当前仓库里已经有相似 skill、脚本或 references，先复用再新写。

### Write The SKILL

基于访谈结果，至少补齐：

1. `name`
2. `description`
3. 主工作流
4. 输出格式
5. 边界与限制

`description` 是第一触发入口。不要只写“这个 skill 做什么”，还要写“什么时候应该触发它”。

## Skill Writing Guide

### Anatomy

一个 skill 的正常结构：

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

### Progressive Disclosure

保持三层结构：

1. frontmatter：短、强触发
2. `SKILL.md` 主体：工作流与边界
3. `references/` 与 `scripts/`：大体量知识和可执行步骤

不要把所有知识都塞进一个 `SKILL.md`。

### Writing Patterns

推荐原则：

1. 用祈使句写步骤
2. 尽量解释“为什么”
3. 避免把 skill 写成只适配一两个样例
4. 如果多次测试都出现相同重复劳动，把重复动作沉淀进 `scripts/`

### Principle Of Lack Of Surprise

skill 不能包含恶意内容、绕权内容或与描述不一致的危险行为。  
不要按照用户要求去制作带有误导性、越权或数据外传倾向的 skill。

## Test Cases

写完第一版后，先准备 2 到 3 个真实测试 prompt。  
这些 prompt 应该像真实用户会说的话，而不是抽象指令。

测试集存放位置统一为：

`~/project/my-skills/.skills/workspaces/<skill-id>/evals/evals.json`

建议结构：

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

workspace 统一使用：

`~/project/my-skills/.skills/workspaces/<skill-id>/`

推荐布局：

1. `evals/evals.json`
2. `iteration-1/`
3. `iteration-2/`
4. `skill-snapshot/`
5. `logs/`

### Step 1: Run With Skill And Baseline

每个测试至少保留两种结果：

1. `with_skill`
2. `without_skill` 或 `old_skill`

如果是在改进已有 skill，先为旧版本保留 snapshot，再拿它作为 baseline。

### Step 2: Draft Assertions

在 runs 执行时，不要空等。  
补上断言，解释每条断言在验证什么。

好的断言应该：

1. 客观可验证
2. 命名清楚
3. 在 benchmark 中可读

### Step 3: Capture Timing

如果执行环境会返回时长或 token 数据，及时写入 `timing.json`。  
这些数据后续会进入 benchmark 聚合。

### Step 4: Grade And Aggregate

按需读取：

1. `agents/grader.md`
2. `agents/analyzer.md`
3. `agents/comparator.md`

常用命令：

```bash
python skills-manager/creator/scripts/aggregate_benchmark.py <workspace>/iteration-N
python skills-manager/creator/eval-viewer/generate_review.py <workspace>/iteration-N --skill-name <name>
```

### Step 5: Read Feedback

用户完成 viewer 审阅后，读取：

`<workspace>/feedback.json`

空反馈通常表示该 case 可以接受；重点修复用户明确指出的问题。

## Improving The Skill

迭代时遵循这些原则：

1. 从反馈中抽象共性，不要只修某一个样例
2. 让 prompt 保持精炼，删除无效负担
3. 尽量把“为什么这样做”写清楚
4. 如果多个 case 都重复造同一类工具，优先把它沉淀进 `scripts/`

常规迭代循环：

1. 修改根目录 `<skill-id>/`
2. 运行下一轮 `iteration-N+1`
3. 重新 viewer 审阅
4. 继续修订，直到结果稳定

## Description Optimization

当 skill 主体已经稳定，再考虑优化 `description`。

步骤如下：

1. 生成一组 should-trigger / should-not-trigger 查询
2. 保存到 `.skills/workspaces/<skill-id>/description-evals.json`
3. 用 review 模板让用户确认 eval set
4. 跑优化循环
5. 回写 `best_description`

命令：

```bash
python skills-manager/creator/scripts/run_loop.py --eval-set ~/project/my-skills/.skills/workspaces/<skill-id>/description-evals.json --skill-path ~/project/my-skills/<skill-id> --model <model> --max-iterations 5 --verbose
```

不要太早做这一步。  
只有当 skill 本体已经比较稳定时，description optimization 才有意义。

## Packaging

当用户需要可分发的 `.skill` 文件时再打包。

默认输出目录：

`~/project/my-skills/.skills/packages/`

命令：

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

7. `scripts/run_eval.py` — 对指定 description 跑触发评测
8. `scripts/improve_description.py` — 基于评测结果用 Claude 生成改进 description
9. `scripts/run_loop.py` — 将 eval + improve 串成迭代循环
10. `scripts/aggregate_benchmark.py` — 聚合多轮评测结果为 benchmark 统计
11. `scripts/generate_report.py` — 将迭代循环结果生成 HTML 报告
12. `scripts/package_skill.py` — 将 skill 打包为 `.skill` 文件（自动创建 `.skills/packages/`）
13. `scripts/quick_validate.py` — skill 基础结构快速校验
14. `scripts/utils.py` — 公共工具函数（frontmatter 解析、路径解析等）

## Finish

子技能完成内容工作后，不要自己做发布。  
统一回到仓库根目录执行：

```bash
bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push
```
