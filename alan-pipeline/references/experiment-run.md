# 实验 Run：可复现 AI 实验协议

当 run 用于跑 AI 训练/评估实验时，在 run.yaml 中加 `experiment:` 字段触发实验协议。
目标：未来任何人拿到 snapshot 目录，都能完整复现整个实验（代码、环境、指标日志）。

## 实验设计哲学（来自 FAIR 方法论）

可复现性解决「能不能重跑」，但更早的问题是：**这个实验值不值得跑？**

在开始执行前，先完成三步思考：

### 步骤一：这个 run 和哪个 run 形成对照？

每个实验 run 都应该和至少一个已有 run 构成**单变量对照**——只改变一件事，其余保持不变。
在 `context:` 中明确写出对比的 run slug 和改变的唯一变量。

避免两种极端：
- **实验太少**：信号不明确，什么也学不到
- **盲目堆实验**：不加思考地最大化资源利用，把所有结果 dump 到 exp card 就觉得 research 做完了

### 步骤二：写下预测

**跑实验前先写预测**，记录在 run.yaml 的可选 `prediction:` 字段：

```yaml
prediction: "预计 top-1 acc 提升约 1.5%，因为 debiasing 消除了系统性低估"
```

- 预测正确 → 你的心智模型是对的，可以沿这个方向继续
- 预测错误 → 这是一个 **surprise**，surprise = 学习信号，说明理解有缺口，要分析原因

### 步骤三：标记 surprise

实验完成后，在对应 exp card 的 frontmatter 中标注结果是否出乎意料：

```yaml
surprise: true
insight: "提升远超预期，可能是因为 long-tail 分布的系统性偏差比预想严重"
```

`surprise: true` 的 exp card 优先分析——意外本身就是最高优先级的信号。

---

## 核心原则

- **Run 内改代码**：本次实验的代码修改在 `alan/runs/<slug>/src/` 内进行，不修改外部代码库。外部代码库只提供组件/工具函数，保持与具体 run 无关。这样多个 run 可以并行运行而互不干扰。
- **数据集路径引用**：大数据集不复制进 run 目录，在 `command` 或 `config` 中用绝对路径引用。
- **单一快照原则**：每次实验的全部状态集中在 `alan/runs/<slug>/snapshot/` 一个目录
- **实验前快照**：代码、环境、配置在启动训练**之前**全部就位
- **Seed 受控**：所有随机性由单一 seed 决定，代码端必须调用 `set_seed()`

## 目录结构

```
alan/runs/<slug>/
  run.yaml                       # Run 定义（含 experiment: 字段）
  progress.md                    # Run 执行历史
  src/                           # ← 本 run 专属实验代码（在这里改）
  snapshot/                      # ← 实验快照根目录（实验前从 src/ 复制）
    metadata.yaml                # 实验元数据（command / seed / config / 结果）
    src/                         # 源码快照（src/ 的只读副本）
    environment/                 # 依赖锁文件
      uv.lock                    # 或 requirements.txt / conda-env.yaml
    logs/
      stdout.log                 # 原始标准输出
      stderr.log                 # 原始标准错误
      metrics.jsonl              # 结构化指标日志（可选，代码自行决定写什么）
```

`src/` 通常从外部代码库复制一份后按本次实验需求修改；外部代码库本身不随实验变动，保持组件化。

## Run YAML（含 experiment: 字段）

```yaml
state: pending

context: |
  模型：Llama-3-8B
  数据集：SynthWiki-32k

instruction: |
  跑 3 seeds (42/43/44) 验证 debiased k=1 精度。
  结果记录到 exp card。

verifier: |
  3 seeds 都跑完？exp card 产出？全部完成 → end，否则 → loop

prediction: "预计 k=1 与 k=5 精度相差 < 0.5%"

experiment:
  command: "python train.py --config configs/base.yaml --seed 42"
  seed: 42
  src: alan/runs/<slug>/src/    # run 专属实验代码目录
  environment: uv           # uv | pip | conda
  config:                   # 超参数完整列表
    lr: 3e-4
    batch_size: 32
    epochs: 100
    model: transformer-base
```

`experiment:` 字段出现 → 执行前必须建快照。

## 实验前检查单（必须在训练启动前完成）

```bash
SLUG=<slug>
SNAP=alan/runs/$SLUG/snapshot

# 1. 建目录
mkdir -p $SNAP/{src,environment,logs}

# 2. 快照 run 专属源码（从 run 目录内的 src/ 复制，不依赖 git 状态）
cp -r alan/runs/$SLUG/src/ $SNAP/src/

# 3. 保存环境文件
cp uv.lock $SNAP/environment/                              # uv
# pip freeze > $SNAP/environment/requirements.txt          # pip
# conda env export > $SNAP/environment/conda-env.yaml      # conda

# 4. 记录当前项目 git commit（外部组件库的版本锚点）
git rev-parse HEAD   # → 填入 metadata.yaml git_commit

# 5. 写 metadata.yaml（见下文模板）

# 6. 确认 metadata.yaml 中 seed 与代码一致
```

> ⚠️ **可复现守则**：实验的可复现性由 `snapshot/src/`（run 专属代码副本）+ `metadata.yaml`（参数 / seed / 数据集路径）共同保证，不依赖外部代码库的 dirty 状态。

## metadata.yaml 完整模板

```yaml
# alan/runs/<slug>/snapshot/metadata.yaml

# ── 必填（实验前） ───────────────────────────────────────
command: "python train.py --config configs/base.yaml --seed 42"
seed: 42

environment:
  manager: uv              # uv | pip | conda
  lock_file: environment/uv.lock
  python: "3.11.9"

config:
  lr: 3e-4
  batch_size: 32
  epochs: 100
  model: transformer-base
  dropout: 0.1
  warmup_steps: 500

# ── 推荐（实验前） ───────────────────────────────────────
git_commit: ""             # git rev-parse HEAD
git_dirty: false           # 有未提交改动时 true
timestamp_start: ""        # ISO 8601
hostname: ""               # uname -n
hardware:
  gpu: ""                  # nvidia-smi --query-gpu=name --format=csv,noheader
  cpu: ""
  ram_gb: 0

# ── 必填（实验后） ───────────────────────────────────────
status: running            # running | completed | failed | killed
timestamp_end: ""
duration_seconds: null

result:
  primary_metric: ""       # 主要指标名
  primary_value: null
  extra: {}                # 其他关键指标

notes: ""                  # 异常观察、调参动机等
```

## 启动实验

```bash
# 重定向原始输出到 snapshot 目录
python train.py ... \
  2>alan/runs/$SLUG/snapshot/logs/stderr.log \
  | tee alan/runs/$SLUG/snapshot/logs/stdout.log
```

训练代码中如何记录指标（写 JSONL、用 wandb、用 tensorboard 还是直接 print）由代码自行决定。

## 实验后更新

1. 更新 `metadata.yaml`：填写 `status`、`timestamp_end`、`duration_seconds`、`result`、`notes`
2. 将关键发现升级为 exp card，card 的 `links:` 引用 `runs/<slug>/snapshot/metadata.yaml`
3. run 完成后 `state: done` 由 CLI 自动写入

## Seed 可复现

代码中必须统一设置所有随机源：

```python
import random, os
import numpy as np
import torch

def set_seed(seed: int):
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(42)  # 在数据加载 / 模型初始化之前调用
```

`metadata.yaml` 的 `seed` 必须与代码中 `set_seed()` 的值一致。

## 复现流程

他人拿到 `snapshot/` 后：

```bash
cd alan/runs/<slug>/snapshot/src/

# 1. 恢复环境
# uv sync --locked（如有 uv.lock）
# pip install -r ../environment/requirements.txt
# conda env create -f ../environment/conda-env.yaml

# 2. 查看 metadata
cat ../metadata.yaml       # command / seed / config

# 3. 用 metadata 中的 command 原样运行
python train.py --config configs/base.yaml --seed 42
```

## 自查清单

执行前确认每项都已完成：

| # | 检查项 | 存储位置 |
|---|--------|----------|
| 1 | `snapshot/src/` 已初始化并完成本次实验修改 | `alan/runs/<slug>/snapshot/src/` |
| 2 | 环境文件已保存 | `snapshot/environment/` |
| 3 | command 已记录 | `snapshot/metadata.yaml` |
| 4 | seed 已记录且代码一致 | `snapshot/metadata.yaml` + `set_seed()` |
| 5 | config 超参数已记录 | `snapshot/metadata.yaml` |
| 6 | git_commit 已填写（外部组件库版本） | `snapshot/metadata.yaml` |
| 7 | 数据集路径已记录且可访问 | `snapshot/metadata.yaml` config 字段 |
