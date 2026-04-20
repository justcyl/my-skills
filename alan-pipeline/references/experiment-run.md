# 实验 Run：可复现 AI 实验的完整协议

当 run 用于跑 AI 训练/评估实验时，使用 `experiment:` 字段触发实验协议。
目标：未来任何人拿到 snapshot 目录，都能完整复现整个实验（代码、环境、指标日志）。

## 核心原则

- **单一快照原则**：每次实验的全部状态集中在 `.pipeline/runs/<slug>.snapshot/` 一个目录
- **实验前快照**：代码、环境、配置在启动训练**之前**全部就位
- **日志即数据**：结构化 JSONL 指标日志是唯一真源，stdout/stderr 仅为补充
- **Seed 受控**：所有随机性由单一 seed 决定，代码端必须调用 `set_seed()`

## 目录结构

```
.pipeline/runs/
  <slug>.yaml                    # Run 定义（含 experiment: 字段）
  <slug>.progress.md             # Run 执行历史
  <slug>.state                   # Run 机器状态
  <slug>.snapshot/               # ← 实验快照根目录
    metadata.yaml                # 实验元数据（command / seed / config / 结果）
    src/                         # 源码快照
    environment/                 # 依赖锁文件
      uv.lock                   # 或 requirements.txt / conda-env.yaml
    logs/
      metrics.jsonl              # 结构化指标日志（JSONL，唯一真源）
      stdout.log                 # 原始标准输出（可选）
      stderr.log                 # 原始标准错误（可选）
```

## Run YAML（含 experiment: 字段）

```yaml
context: |
  模型：Llama-3-8B
  数据集：SynthWiki-32k

instruction: |
  跑 3 seeds (42/43/44) 验证 debiased k=1 精度。
  结果记录到 exp card。

verifier: |
  3 seeds 都跑完？exp card 产出？全部完成 → end，否则 → loop

experiment:
  command: "python train.py --config configs/base.yaml --seed 42"
  seed: 42
  src: src/                 # 要快照的源码目录（相对项目根）
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
SNAP=.pipeline/runs/$SLUG.snapshot

# 1. 建目录
mkdir -p $SNAP/{src,environment,logs}

# 2. 快照源码（推荐 git archive，干净无临时文件）
git archive HEAD | tar -x -C $SNAP/src/
# 或：cp -r src/ $SNAP/src/

# 3. 保存环境文件
cp uv.lock $SNAP/environment/                              # uv
# pip freeze > $SNAP/environment/requirements.txt          # pip
# conda env export > $SNAP/environment/conda-env.yaml      # conda

# 4. 检查 git 状态
git rev-parse HEAD   # → 填入 metadata.yaml git_commit
git status --short   # 有输出 → git_dirty: true，强烈建议先 commit

# 5. 写 metadata.yaml（见下文模板）

# 6. 确认 metadata.yaml 中 seed 与代码一致
```

> ⚠️ **可复现守则**：若 `git_dirty: true`，`src/` 快照比 git commit 更重要——它记录了实际运行的代码。强烈建议实验前先 `git commit`。

## metadata.yaml 完整模板

```yaml
# .pipeline/runs/<slug>.snapshot/metadata.yaml

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

## 训练代码：结构化日志

在训练代码中使用 logger 组件库将指标写入 `logs/metrics.jsonl`。
这是日后回放、对比实验的唯一数据源。

```python
import sys, os
sys.path.insert(0, os.path.expanduser(
    "~/.agents/skills/alan-pipeline/scripts"))

from components import ExpLogger, JSONLBackend, ConsoleBackend

SNAP = ".pipeline/runs/<slug>.snapshot"

with ExpLogger(name="<slug>", backends=[
    JSONLBackend(f"{SNAP}/logs/metrics.jsonl"),        # 持久化（必须）
    ConsoleBackend(verbose="compact", keys=["loss"]),  # 可选 stdout
]) as logger:
    logger.config(lr=3e-4, model="transformer", seed=42)
    for step in range(num_steps):
        loss = train_step()
        logger.log(step=step, loss=loss, accuracy=acc)
    logger.event("training complete")
```

**关键点：**
- `JSONLBackend` 始终开启——它是回放和 watch 的数据源
- `ConsoleBackend` 可选——仅用于终端阅读
- 训练代码**不 import Rich**——显示逻辑在 watch/replay 侧

可选添加 wandb/tensorboard backend：

```python
from components import WandbBackend, TensorBoardBackend

# 在 backends 列表中追加：
WandbBackend(project="my-project", name="<slug>")
TensorBoardBackend(log_dir=f"{SNAP}/logs/tb")
```

完整 API 见 [logger-components.md](logger-components.md)，
组合示例见 [logger-recipes.md](logger-recipes.md)，
wandb 深度用法见 [logger-wandb.md](logger-wandb.md)。

## 启动实验

```bash
# 同时重定向原始输出到 snapshot 目录
python train.py ... \
  2>.pipeline/runs/$SLUG.snapshot/logs/stderr.log \
  | tee .pipeline/runs/$SLUG.snapshot/logs/stdout.log
```

## 实时监控（另一个终端）

```bash
# 实时 TUI（训练中，tail JSONL）
python ~/.agents/skills/alan-pipeline/scripts/watch.py \
  .pipeline/runs/<slug>.snapshot/logs/metrics.jsonl

# 回放（训练后）
python ~/.agents/skills/alan-pipeline/scripts/replay.py \
  .pipeline/runs/<slug>.snapshot/logs/metrics.jsonl --speed 8
```

watch 和训练谁先启动都可以——watch 会等待文件出现。

## 实验后更新

1. 更新 `metadata.yaml`：填写 `status`、`timestamp_end`、`duration_seconds`、`result`、`notes`
2. 将关键发现升级为 exp card，card 的 `links:` 引用 `runs/<slug>.snapshot/metadata.yaml`
3. 在 run 的 `progress.md` 中记录实验 slug

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

他人拿到 `<slug>.snapshot/` 后：

```bash
cd <slug>.snapshot/src/

# 1. 恢复环境
# uv sync --locked（如有 uv.lock）
# pip install -r ../environment/requirements.txt
# conda env create -f ../environment/conda-env.yaml

# 2. 查看 metadata
cat ../metadata.yaml       # command / seed / config

# 3. 用 metadata 中的 command 原样运行
python train.py --config configs/base.yaml --seed 42

# 4. 对比指标日志
python replay.py ../logs/metrics.jsonl --speed 0
```

## 自查清单

执行前确认每项都已完成：

| # | 检查项 | 存储位置 |
|---|--------|----------|
| 1 | 源码已快照 | `snapshot/src/` |
| 2 | 环境文件已保存 | `snapshot/environment/` |
| 3 | command 已记录 | `snapshot/metadata.yaml` |
| 4 | seed 已记录且代码一致 | `snapshot/metadata.yaml` + `set_seed()` |
| 5 | config 超参数已记录 | `snapshot/metadata.yaml` |
| 6 | git_commit 已填写 | `snapshot/metadata.yaml` |
| 7 | git_dirty 为 false | `git status --short` 无输出 |
| 8 | JSONLBackend 已配置 | 训练代码中指向 `snapshot/logs/metrics.jsonl` |
