# Create Flow

当任务是"新建或重写 skill / 从对话轨迹沉淀 skill"时读取本文件。

## Capture Intent

优先从当前对话里提炼信息，不要机械重复询问已经明确的内容。

至少要搞清楚：

1. 这个 skill 应该让模型完成什么任务
2. 它应该在什么场景下触发（哪些措辞或语境）
3. 输出格式或交付物是什么
4. 是否需要后续评测

对于客观可验证的任务（文件转换、结构化提取、固定工作流生成），默认建议加测试集。
对于主观性强的任务（风格化写作），默认可以先不做硬性断言。

## Interview And Research

主动追问：

1. 边界情况
2. 输入输出样例
3. 成功标准
4. 依赖和工具约束

如果当前仓库里已经有相似 skill、脚本或 references，先复用再新写。可以用 MCP 做并行调研。

## Working Root

默认仓库：`~/project/my-skills`。如果目标 skill 尚不存在，先让 manager 运行：

```bash
bash skills-manager/scripts/create_skill.sh --skill-id <id> --name <name> --description <description>
```

直接编辑仓库根目录 `<skill-id>/`：

1. `<skill-id>/SKILL.md`
2. `<skill-id>/references/*.md`
3. `<skill-id>/scripts/*`

评测与中间产物放 `.skills/workspaces/<skill-id>/`，不要把真实内容写到 `.skills/`。

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

## Default Flow

1. 先确认 manager 已创建好骨架（或请 manager 运行 `create_skill.sh`）
2. 通过问答明确需求（见 Capture Intent）
3. 写出最小可用的 `SKILL.md`
4. 按需要补 `references/` 与 `scripts/`
5. 如果用户只要快速落地，到这里即可交回 manager finalize：
   ```bash
   bash skills-manager/scripts/sync_skill_state.sh --skill-id <id> --push
   ```
6. 如果用户要求验证或长期维护，再进入 `references/eval.md`

## Preparing Test Cases

> **按需执行**：仅在用户明确要求验证时才执行。不是默认步骤。

写完第一版后，先准备 2 到 3 个真实测试 prompt，像真实用户会说的话，而不是抽象指令。

存放位置：`~/project/my-skills/.skills/workspaces/<skill-id>/evals/evals.json`

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

## Packaging

当用户需要可分发的 `.skill` 文件时再打包，默认输出到 `~/project/my-skills/.skills/packages/`：

```bash
python skills-manager/creator/scripts/package_skill.py ~/project/my-skills/<skill-id>
```
