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
核心设计：**数据与显示完全解耦**。

## 设计原则

```
训练代码（train.py）         外部监控（另一个终端）
  │                            │
  │  ExpLogger                 │  watch.py / replay.py
  │  ├─ JSONLBackend → disk    │  └─ tail JSONL → TUIDashboard
  │  └─ ConsoleBackend → stdout│
  │                            │
  ▼                            ▼
  runs/exp.jsonl              Rich Live TUI
  (持久化，唯一真源)            (外挂，随时启动)
```

**训练代码只记录数据，不负责显示逻辑。**
- 训练侧：`JSONLBackend`（持久化）+ `ConsoleBackend`（可选 stdout）
- 监控侧：`watch.py`（实时）或 `replay.py`（回放）读 JSONL 渲染 TUI
- 两侧完全独立，训练代码无需 import Rich

## 组件地图

```
scripts/
  components/
    base.py                  MetricFrame + Backend ABC（数据契约）
    backend_jsonl.py         JSONL 文件 backend（持久化，始终开启）
    backend_console.py       纯文本 stdout backend（full / compact / silent）
    backend_wandb.py         wandb backend（可选）
    backend_tensorboard.py   TensorBoard backend（可选）
    tui_dashboard.py         Rich Live TUI（仅被 watch/replay 使用）
    logger.py                ExpLogger 组装器
  watch.py                   实时 TUI 监控（tail JSONL 文件）
  replay.py                  回放 CLI（从 JSONL 文件重现 TUI）
```

## 快速接线

**训练代码侧：只记录，不显示**

```python
import sys
sys.path.insert(0, "path/to/exp-logger/scripts")
from components import ExpLogger, JSONLBackend, ConsoleBackend

with ExpLogger(name="run-1", backends=[
    JSONLBackend("runs/run-1.jsonl"),              # 持久化（必须）
    ConsoleBackend(verbose="compact", keys=["loss", "accuracy"]),  # 可选 stdout
]) as logger:
    logger.config(lr=3e-4, model="transformer")
    for epoch in range(100):
        logger.log(step=epoch, loss=loss, accuracy=acc)
    logger.event("training complete")
```

**监控侧：另一个终端，外挂 TUI**

```bash
# 实时监控（训练中）
python exp-logger/scripts/watch.py runs/run-1.jsonl

# 回放（训练后）
python exp-logger/scripts/replay.py runs/run-1.jsonl --speed 8
```

训练先启动或 watch 先启动都可以——watch.py 会等待文件出现，然后从头追赶。

## 典型场景

### 场景 A：本地开发，双终端

```
Terminal 1:  python train.py          # 输出 compact console + 写 JSONL
Terminal 2:  python watch.py runs/exp.jsonl  # 实时 TUI
```

### 场景 B：CI / 服务器，无 TUI

```python
with ExpLogger(name="run", backends=[
    JSONLBackend("runs/run.jsonl"),
    ConsoleBackend(verbose="compact", keys=["loss"]),
]) as logger:
    ...
# 事后回放：python replay.py runs/run.jsonl --speed 0
```

### 场景 C：同步 wandb

```python
from components import ExpLogger, JSONLBackend, ConsoleBackend, WandbBackend

with ExpLogger(name="run", backends=[
    JSONLBackend("runs/run.jsonl"),
    ConsoleBackend(verbose="compact", keys=["loss"]),
    WandbBackend(project="my-project"),
]) as logger:
    ...
```

### 场景 D：from_config

```python
cfg = {
    "name": "run-1",
    "logdir": "runs",
    "console": "compact",
    "console_keys": ["loss", "accuracy"],
    "wandb": {"project": "my-project"},   # None = 不用
}
with ExpLogger.from_config(cfg) as logger:
    ...
```

## 实时监控 watch.py

```bash
python exp-logger/scripts/watch.py <file.jsonl>
python exp-logger/scripts/watch.py <file.jsonl> --poll 0.2   # 轮询间隔
```

- 文件不存在时自动等待
- 从头读取已有数据（追赶），然后 tail 新数据
- 训练结束（收到 `_type: done`）后 hold 最终画面 2 秒退出
- 无数据 10 分钟后自动退出

## 回放 replay.py

```bash
python exp-logger/scripts/replay.py runs/run.jsonl
python exp-logger/scripts/replay.py runs/run.jsonl --speed 8   # 8x
python exp-logger/scripts/replay.py runs/run.jsonl --speed 0   # 即时
```

## 自定义 Backend

```python
from components import Backend, MetricFrame

class SlackBackend(Backend):
    def write(self, frame: MetricFrame) -> None:
        if frame.get("_type") == "event":
            send_slack(frame["msg"])
    def close(self) -> None: pass
```

## 参考文档

- `references/components.md` — 每个组件的完整 API
- `references/recipes.md`    — 更多组合示例
- `references/integration-wandb.md` — wandb 深度集成

## 依赖

| 组件 | 训练侧 | 监控侧 |
|------|---------|--------|
| JSONLBackend | 无（标准库）| — |
| ConsoleBackend | 无（标准库）| — |
| WandbBackend | `pip install wandb` | — |
| TensorBoardBackend | `pip install tensorboard` | — |
| watch.py / replay.py | — | `pip install rich` |
