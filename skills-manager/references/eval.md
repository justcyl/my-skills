# Eval Flow

> **按需执行**：本流程仅在用户明确要求评测时才启动，不是创建 skill 的默认步骤。

当任务是"验证、迭代、benchmark、viewer 审阅或盲评"时读取本文件。

子代理通过 **pi-subagent** skill 调度，参见 `pi-subagent/SKILL.md` 了解 pane_split / invoke / wait_agent 调用方式。

## 适用范围

本流程适用于**函数型 skill**：给定输入，产出可保存的文件或文本产物（HTML、图片、文档、报告、代码等），执行本身没有破坏性副作用。典型例子：academic-blog、gemini-image-gen、officecli、cli-creator。

**不适用以下两类 skill，不要对它们启动本流程：**

1. **过程型 / 编排型 skill**：执行即副作用，成功标志是操作序列而非产物文件。例如 skills-manager（修改仓库状态）、lark（发消息/写文档）、overleaf（推送到远端）、pi-subagent（管理 pane）、alan-pipeline（写 card/run）。强行跑 eval 会触发真实操作，cleanup 代价高，且 with-skill vs baseline 的产出文本区分度极低。

2. **依赖外部写操作的 API wrapper**：调用会产生不可回滚的写操作（发帖、发邮件、创建记录）。只读 API（web-reader、bilibili-cli、axonhub 查询）可以接受，但断言应针对结构而非内容（“返回了 JSON 且包含 title 字段”而非“标题是 X”）。

## Workspace

统一使用：`~/project/my-skills/.skills/workspaces/<skill-id>/`

推荐结构：

1. `evals/evals.json`
2. `iteration-1/`
3. `iteration-2/`
4. `skill-snapshot/`
5. `logs/`

## Default Eval Loop

1. 设计 2-3 个真实测试 prompt
   如果被测 skill 是路由型（包含多条路由分支），测试集必须覆盖每条路由分支，并包含至少一个跨分支的歧义 case
2. 在 workspace 下写 `evals/evals.json`
3. 对每个 case 同时跑 with-skill 与 baseline（同一轮）
4. 补 assertions 与 grading
5. 聚合 benchmark
6. 生成 viewer 让用户审阅——先给用户看，不要自己先评估
7. 根据反馈修改根目录 `<skill-id>/`
8. 每轮迭代改完后，执行 `bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push`
9. 继续下一轮，直到满意为止

## Step 1: Run With Skill And Baseline

**关键：所有 pane 必须在同一轮中 split 并启动。** 不要等 with-skill 跑完再启动 baseline——两组并行，同时开始，一起等待完成。

通过 pi-subagent 为每个 test case 各 split 两个 pane（with-skill / baseline），在同一轮全部 run，然后 wait_agent 等待全部完成。

**with-skill run prompt：**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files or "none">
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/with_skill/outputs/
- Outputs to save: <what user cares about>
```

**baseline run：**

- 新建 skill：不使用任何 skill，同样 prompt，输出到 `without_skill/outputs/`
- 改进已有 skill：使用旧版本 snapshot（`cp -r <skill-path> <workspace>/skill-snapshot/`），输出到 `old_skill/outputs/`

**Baseline 选择原则：**
新建 skill 始终用 `without_skill` 作为 baseline，跨所有迭代保持不变。改进已有 skill 时，以用户最初带来的版本作为固定 baseline，而不是切换为上一迭代。

**目录命名：** eval 目录用描述性名称，不要用 `eval-0`。根据测试内容命名（如 `import-github-url`、`create-from-trace`），目录名与 `eval_name` 保持一致。

为每个 test case 创建 `eval_metadata.json`：

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

## Step 2: Draft Assertions

在 runs 执行时，不要空等，补上断言。

好的断言应该：

1. 客观可验证
2. 命名清楚（在 benchmark viewer 中可读，让人一眼理解在验证什么）
3. 有区分度——如果 with_skill 和 baseline 都一定通过，这条断言没意义

对于主观性强的 skill，跳过硬性断言。

更新 `eval_metadata.json` 和 `evals/evals.json` 中的 assertions，然后向用户解释他们将会看到什么。

## Step 3: Capture Timing

每个 subagent 任务完成后，通知中会包含 `total_tokens` 和 `duration_ms`。立即保存到 `timing.json`——这些数据不会被持久化到其他地方，事后无法恢复。

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

## Step 4: Grade, Aggregate, Launch Viewer

**Grade 每个 run：**

读 `agents/grader.md` 了解评分规则。直接调用 pi 启动 grader（grader.md 同时充当 system prompt）：

```bash
pi --system-prompt ~/project/my-skills/skills-manager/agents/grader.md \
   --no-skills --no-context-files --no-session --print \
   "<grading task>"
```

输出保存到 `grading.json`，字段必须精确使用 `text`、`passed`、`evidence`（不是 `name`/`met`/`details`），viewer 依赖这些字段名。对于可编程验证的断言，写脚本而不是目测——脚本更快、更可靠，可以跨迭代复用。

**Aggregate：**

```bash
python skills-manager/eval-scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>
```

输出 `benchmark.json` 和 `benchmark.md`，包含 pass_rate、时间、token 用量的均值 ± 标准差和 delta。with_skill 放在 baseline 前面。

**Analyst pass：**

同样直接调用 pi：

```bash
pi --system-prompt ~/project/my-skills/skills-manager/agents/analyzer.md \
   --no-skills --no-context-files --no-session --print \
   "<benchmark summary>"
```

对聚合结果做模式分析——找出无区分度的断言、高方差 eval、时间/token 权衡。

**Launch viewer（先给用户看，不要自己先评估）：**

生成 viewer 并等待用户审阅，不要在用户看到结果之前自己先判断输出好坏——用户的第一手反馈是改进的起点。

```bash
nohup python skills-manager/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
VIEWER_PID=$!
```

迭代 2+ 时加 `--previous-workspace <workspace>/iteration-<N-1>`。

无浏览器环境下使用 `--static <output_path>` 生成独立 HTML。

告诉用户："结果已在浏览器中打开。'Outputs' 标签展示每个 test case 的输出供你反馈；'Benchmark' 标签展示定量对比。看完后告诉我。"

## Step 5: Read Feedback

用户完成 viewer 审阅后，读取 `<workspace>/feedback.json`：

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
2. **保持 prompt 精炼**：删除没有贡献的内容。读执行轨迹，不只是最终输出——如果 skill 让模型浪费时间在无效操作上，删掉导致这些操作的部分
3. **解释原因**：今天的模型有很好的心智理论。解释为什么比死板的结构更有效。如果发现自己在写 ALWAYS 或 NEVER，这是黄色警告——用解释代替口号
4. **沉淀重复劳动**：如果所有测试 case 里的 subagent 都独立写了类似的辅助脚本，把这个脚本放进 `scripts/` 一次性解决

### The Iteration Loop

1. 修改根目录 `<skill-id>/`
2. 运行下一轮 `iteration-N+1`（所有 test case，包含 baseline）
3. 用 viewer 审阅（加 `--previous-workspace` 对比上轮）
4. 读反馈，继续修订
5. 每轮迭代改完后，执行 `bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push`
6. 继续循环，直到：用户满意、所有反馈为空、或没有实质进展

## Advanced: Blind Comparison

当需要严格对比两个 skill 版本时，读 `agents/comparator.md` 和 `agents/analyzer.md`。

做法：把两个版本的输出匿名交给独立 agent，不透露哪个是新版哪个是旧版，让它独立判断。然后用 analyzer 分析赢家赢在哪里。两者都通过 `pi --system-prompt` 直接调用（见 Step 4 的模式）。

这是可选的高级功能，大多数场景不需要。

## Notes

1. 根目录 `<skill-id>/` 是唯一真源，workspace 只存评测过程与中间结果
2. 每轮修改结束后，执行 `bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push` 提交推送
