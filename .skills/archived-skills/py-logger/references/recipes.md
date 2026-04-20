# Recipes — 常见组合方式

根据场景选择组合，从最简单到最完整。

---

## Recipe 1：最简（只写 JSONL，纯文本输出）

适合 CI / 服务器 / 无 tty 环境。

```python
from exp_logger.components import ExpLogger, JSONLBackend, ConsoleBackend

logger = ExpLogger(
    name="run-1",
    backends=[
        JSONLBackend("runs/run-1.jsonl"),
        ConsoleBackend(verbose="compact", keys=["loss", "accuracy"]),
    ]
)
```

---

## Recipe 2：本地开发带 TUI

适合在终端里直接看 dashboard。

```python
from exp_logger.components import ExpLogger, JSONLBackend, TUIDashboard

logger = ExpLogger(
    name="run-1",
    backends=[
        JSONLBackend("runs/run-1.jsonl"),
        TUIDashboard(),
    ]
)
```

---

## Recipe 3：TUI + wandb 同步

```python
from exp_logger.components import ExpLogger, JSONLBackend, TUIDashboard, WandbBackend

logger = ExpLogger(
    name="run-1",
    backends=[
        JSONLBackend("runs/run-1.jsonl"),
        WandbBackend(project="my-project", name="run-1"),
        TUIDashboard(),
    ]
)
```

---

## Recipe 4：TUI + TensorBoard 同步

```python
from exp_logger.components import ExpLogger, JSONLBackend, TUIDashboard, TensorBoardBackend

logger = ExpLogger(
    name="run-1",
    backends=[
        JSONLBackend("runs/run-1.jsonl"),
        TensorBoardBackend(log_dir="runs/tb/run-1"),
        TUIDashboard(),
    ]
)
```

---

## Recipe 5：from_config（argparse / hydra / yaml 友好）

不在代码里硬写 backend 列表，由 config 控制。

```python
# train.py
import argparse
from exp_logger.components import ExpLogger

parser = argparse.ArgumentParser()
parser.add_argument("--logdir",  default="runs")
parser.add_argument("--tui",     action="store_true")
parser.add_argument("--wandb-project", default=None)
args = parser.parse_args()

cfg = {
    "name":   "run-1",
    "logdir": args.logdir,
    "tui":    "auto",                          # tty 检测
    "wandb":  {"project": args.wandb_project} if args.wandb_project else None,
    "console": "compact",
    "console_keys": ["loss", "accuracy"],
}

with ExpLogger.from_config(cfg) as logger:
    logger.config(lr=3e-4, model="transformer")
    for step in range(1000):
        logger.log(step=step, loss=..., accuracy=...)
    logger.event("training complete")
```

`from_config` 的字段：

| 字段            | 类型             | 默认        | 说明                         |
|---------------|-----------------|------------|------------------------------|
| name          | str             | "exp"      | 实验名称                     |
| logdir        | str             | "runs"     | JSONL 目录                   |
| tui           | bool \| "auto"  | "auto"     | TUI 开关；auto = tty 检测    |
| wandb         | dict \| None    | None       | 传给 WandbBackend 的参数     |
| tensorboard   | str \| None     | None       | TensorBoard log_dir          |
| console       | str             | "full"     | "full"/"compact"/"silent"    |
| console_keys  | list[str]       | None       | compact 模式显示的 keys       |

---

## Recipe 6：自定义 Backend（扩展点）

继承 `Backend`，实现 `write` 和 `close`：

```python
from exp_logger.components import Backend, MetricFrame, ExpLogger, JSONLBackend

class SlackBackend(Backend):
    """每 50 步发一条 Slack 消息。"""
    def __init__(self, webhook_url: str):
        self._url = webhook_url

    def write(self, frame: MetricFrame) -> None:
        if frame.get("_type") == "metric" and frame.get("step", 0) % 50 == 0:
            import requests
            loss = frame.get("loss", "?")
            requests.post(self._url, json={"text": f"step {frame['step']}  loss={loss}"})

    def close(self) -> None:
        pass


logger = ExpLogger(
    name="run-1",
    backends=[
        JSONLBackend("runs/run-1.jsonl"),
        SlackBackend("https://hooks.slack.com/..."),
    ]
)
```

---

## Recipe 7：实验结束后回放

```bash
# 在终端里以 8x 速度回放
python exp_logger/scripts/replay.py runs/run-1_20260419.jsonl --speed 8

# 慢放关键阶段
python exp_logger/scripts/replay.py runs/run-1_20260419.jsonl --speed 0.5

# 即时（无延迟，快速浏览最终状态）
python exp_logger/scripts/replay.py runs/run-1_20260419.jsonl --speed 0
```

或在 Python 里嵌入回放：

```python
import json, time
from exp_logger.components import TUIDashboard, MetricFrame

frames = [MetricFrame(json.loads(l)) for l in open("runs/run-1.jsonl")]
dash = TUIDashboard(name="run-1 [replay 4x]", replay_speed=4)
dash.start()
t0_wall = time.time()
t0_log  = frames[0].get("t", t0_wall)
for i, f in enumerate(frames):
    if i > 0:
        lag = f.get("t", t0_log) - t0_log
        sleep = lag / 4 - (time.time() - t0_wall)
        if sleep > 0: time.sleep(sleep)
    dash.push(f)
time.sleep(3)
dash.stop()
```
