---
name: fair-experiment-tracker
description: "基于 FAIR（Meta AI Research）凯明（Kaiming He）实验管理方法论的实验追踪表格生成技能。当用户需要：设计实验追踪表格、管理机器学习/深度学习实验、记录和对比实验结果、建立实验对照组、系统化 research workflow、创建 ablation study 表格、或任何涉及"实验管理""实验记录""实验对比""research spreadsheet""实验表格"的请求时，使用此技能。即使用户只是说'帮我管理实验'或'我想系统化我的研究流程'，也应触发此技能。"
---

# FAIR 实验追踪表格生成器

## 核心理念

这个技能源自 FAIR 内部的实验管理哲学——凯明（Kaiming He）教导实习生的第一课就是：**学会用 Excel 表格管理实验**。

好的研究不是满屏代码，而是盯着一张精心设计的表格，去理解每一行代表什么。表格的设计本身就是 research 能力的体现。

### 两种糟糕的实验模式（要避免）

1. **实验太少**：信号不明确，什么也学不到
2. **盲目跑实验**：不加思考地最大化资源利用率，把所有结果 dump 到表格里就觉得 research 做完了

### 正确的实验管理哲学

- **每一行都要与其他行发生关系**——对照式对比产生梯度信号
- **跑实验前先做预测**——预测对了，说明思维链可以继续延伸；预测错了，这个 surprise 本身就是信号
- **精心选择列（metrics）和行（experiments）**——不是所有结果都值得放进表格

## 工作流程

### Step 1: 需求收集

与用户确认以下信息：

1. **研究领域**：CV / NLP / RL / 多模态 / 其他
2. **实验类型**：Ablation Study / 超参搜索 / 架构对比 / 方法对比 / 数据集实验
3. **关注的核心指标**：准确率、loss、FLOPs、推理速度、参数量等
4. **基线方案**（Baseline）：已有的基线是什么
5. **实验变量**：哪些因素要对比（如学习率、模型大小、数据增强策略等）

如果用户没有明确指定，根据研究领域提供合理默认值。

### Step 2: 读取生成脚本并运行

读取 `scripts/generate_tracker.py` 脚本的内容，根据用户需求修改配置参数后执行。

脚本路径：当前技能目录下的 `scripts/generate_tracker.py`

运行方式：
```bash
python scripts/generate_tracker.py \
  --domain "cv" \
  --experiment_type "ablation" \
  --output "/mnt/user-data/outputs/experiment_tracker.xlsx"
```

支持的参数：
- `--domain`: 研究领域 (cv, nlp, rl, multimodal, general)
- `--experiment_type`: 实验类型 (ablation, hyperparam, architecture, method, dataset)
- `--output`: 输出文件路径
- `--project_name`: 项目名称（可选）
- `--baseline_name`: 基线名称（可选）
- `--num_experiment_rows`: 预留的实验行数，默认 20

### Step 3: 交付与说明

将生成的 xlsx 文件交付给用户，并说明：

1. **表格结构解读**：每个 sheet 的用途
2. **如何使用「预测」列**：跑实验前先填写预期结果
3. **如何用条件格式快速发现异常**
4. **实验编排建议**：怎样让每一行都产生梯度信号

## 表格设计原则（参考 `references/design_principles.md`）

核心设计原则已写入参考文件。在生成表格时，务必先阅读该文件以确保遵循所有原则。

## 关键提醒

- 表格不只是记录工具，它是**思考工具**——设计表格的过程就是在做 research decision
- 每新增一行实验，都要思考：它和表格中已有的哪一行构成对照？
- 「预测」列是灵魂——没有预测的实验等于盲人摸象
- 表格应该能讲故事：从上到下读，应该能看到一条清晰的探索路径
