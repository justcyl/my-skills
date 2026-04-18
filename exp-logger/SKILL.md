---
name: exp-logger
description: >
  为 Python 训练程序提供可组合的实验日志与 TUI 监控组件库。
  当用户需要训练日志、实验可视化、TUI dashboard、TUI 指标回放、
  wandb 或 tensorboard 集成时使用。
  触发语境：「做个训练 logger」「给我写个实验日志系统」「加个 wandb 集成」
  「训练过程可视化」「dashboard 监控训练」「实验回放」「TUI 监控」。
---

# exp-logger

为 Python 实验训练程序提供**可组合的日志组件库**。
核心设计：**数据与显示完全解耦**，按需组合 backend，不硬编码任何实现。

## 组件地图

```
scripts/components/
  base.py                  MetricFrame + Backend ABC（数据契约 + 接口）
  backend_jsonl.py         JSONL 文件 backend（持久化 / 回放数据源）
  backend_console.py       纯文本 stdout backend（full / compact / silent）
  backend_wandb.py         wandb backend（可选，需 pip install wandb）
  backend_tensorboard.py   TensorBoard backend（可选）
  tui_dashboard.py         Rich Live TUI dashboard（可选，需 pip install rich）
  logger.py                ExpLogger 组装器（把任意 backend 列表串联）
scripts/
  replay.py                回放 CLI（从 JSONL 文件重现 TUI）
```

所有组件路径：`exp-logger/scripts/components/`

---

## 快速接线

**第一步**：把 `exp-logger/scripts/` 目录复制到项目中（或直接引用 skill 路径）。

```python
import sys
sys.path.insert(0, "path/to/exp-logger/scripts")
from components import ExpLogger, JSONLBackend, TUIDashboard, WandbBackend
```

**第二步**：选择场景（见下方），或用 `from_config` 统一管理。

---

## 四种典型场景

### 场景 A：本地开发，带 TUI dashboard

```python
from components import ExpLogger, JSONLBackend, TUIDashboard

with ExpLogger(name="run-1", backends=[
    JSONLBackend("runs/run-1.jsonl"),   # 始终保留，用于回放
    TUIDashboard(),                      # Rich Live dashboard
]) as logger:
    logger.config(lr=3e-4, model="transformer-base")
    for step in range(1000):
        logger.log(step=step, loss=loss, accuracy=acc, lr=lr)
    logger.event("training complete")
```

### 场景 B：CI / 服务器，纯文本日志

```python
from components import ExpLogger, JSONLBackend, ConsoleBackend

with ExpLogger(name="run-1", backends=[
    JSONLBackend("runs/run-1.jsonl"),
    ConsoleBackend(verbose="compact", keys=["loss", "accuracy"]),
]) as logger:
    ...
```

### 场景 C：同步 wandb

```python
from components import ExpLogger, JSONLBackend, TUIDashboard, WandbBackend

with ExpLogger(name="run-1", backends=[
    JSONLBackend("runs/run-1.jsonl"),
    WandbBackend(project="my-project"),
    TUIDashboard(),
]) as logger:
    ...
```

### 场景 D：from_config（argparse / hydra / yaml 友好）

```python
from components import ExpLogger

cfg = {
    "name":   "run-1",
    "logdir": "runs",
    "tui":    "auto",                          # tty 则开 TUI，否则纯文本
    "wandb":  {"project": "my-project"},       # None = 不用 wandb
    "console": "compact",
    "console_keys": ["loss", "accuracy"],
}

with ExpLogger.from_config(cfg) as logger:
    logger.config(lr=3e-4, ...)
    for step in range(1000):
        logger.log(step=step, loss=..., accuracy=...)
    logger.event("training complete")
```

---

## 回放

训练结束后，用 JSONL 文件回放 TUI：

```bash
python exp-logger/scripts/replay.py runs/run-1_20260419.jsonl
python exp-logger/scripts/replay.py runs/run-1_20260419.jsonl --speed 8   # 8x 加速
python exp-logger/scripts/replay.py runs/run-1_20260419.jsonl --speed 0   # 即时
```

---

## 自定义 Backend

任何地方都可以通过继承 `Backend` 扩展：

```python
from components import Backend, MetricFrame

class MyBackend(Backend):
    def write(self, frame: MetricFrame) -> None:
        if frame.get("_type") == "event":
            send_slack(frame["msg"])

    def close(self) -> None: pass
```

然后直接加入 `backends` 列表即可。

---

## 参考文档

- `references/components.md` — 每个组件的完整 API
- `references/recipes.md`    — 更多组合示例（7 种）
- `references/integration-wandb.md` — wandb 深度集成（sweep / offline / resume）

---

## 依赖

| 组件               | 依赖           |
|------------------|----------------|
| JSONLBackend      | 无（标准库）   |
| ConsoleBackend    | 无（标准库）   |
| WandbBackend      | `pip install wandb` |
| TensorBoardBackend| `pip install tensorboard` |
| TUIDashboard      | `pip install rich` |
| replay.py         | `pip install rich` |
