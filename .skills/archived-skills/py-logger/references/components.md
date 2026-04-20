# Component API Reference

exp-logger 的核心是一个**组件库**，所有功能由可独立组合的 Python 类提供。
不同于硬编码方案，你可以自由选择和替换任意 Backend。

## 数据流

```
训练脚本
  logger.log(step, loss, acc)
       │
       │  MetricFrame (typed dict)
       ▼
  ExpLogger._broadcast()
       │
       ├──→ JSONLBackend      → runs/exp.jsonl        （持久化 / 回放数据源）
       ├──→ WandbBackend      → wandb.log(...)        （可选）
       ├──→ TensorBoardBackend→ writer.add_scalar(...) （可选）
       └──→ TUIDashboard      → Rich Live thread       （可选，默认开）
               或
            ConsoleBackend   → stdout 纯文本          （无 tty 时替代 TUI）
```

---

## MetricFrame

`dict` 的子类，核心数据契约。

```python
from exp_logger.components import MetricFrame

MetricFrame.metric(step=10, loss=1.23, accuracy=0.85)
MetricFrame.event(step=10, msg="checkpoint saved")
MetricFrame.config(lr=3e-4, model="transformer")
MetricFrame.done(step=200, elapsed=16.3)
```

保留字段（Backend 可读取）：

| 字段     | 类型    | 说明                          |
|---------|---------|-------------------------------|
| `_type` | str     | "init"/"config"/"metric"/"event"/"done" |
| `step`  | int     | 训练步数                      |
| `t`     | float   | UTC epoch                     |
| `msg`   | str     | event 内容                    |
| ...     | any     | 用户自定义字段（scalar/string）|

---

## Backend ABC

所有 backend 实现两个方法：

```python
class Backend(ABC):
    def write(self, frame: MetricFrame) -> None: ...   # 必须线程安全
    def close(self) -> None: ...                       # 必须幂等
```

---

## JSONLBackend

```python
from exp_logger.components import JSONLBackend

backend = JSONLBackend(path="runs/exp.jsonl")
```

- 每帧追加一行 JSON，行缓冲（进程崩溃不丢数据）
- `backend.path` → `Path` 对象
- **建议始终开启**，是回放功能的数据源
- 无额外依赖

---

## ConsoleBackend

```python
from exp_logger.components import ConsoleBackend

# 默认：每步打印所有字段
backend = ConsoleBackend()

# compact：只打印指定 keys
backend = ConsoleBackend(verbose="compact", keys=["loss", "accuracy"])

# silent：只打印 event / done
backend = ConsoleBackend(verbose="silent")

# 写到文件
backend = ConsoleBackend(file=open("train.log", "w"))
```

参数：

| 参数      | 类型                          | 默认    |
|---------|-------------------------------|---------|
| verbose | "full" \| "compact" \| "silent" | "full"  |
| keys    | list[str] \| None             | None    |
| file    | IO                            | sys.stdout |

---

## WandbBackend

需要 `pip install wandb`。

```python
from exp_logger.components import WandbBackend

# 新建 run
backend = WandbBackend(project="my-project")
backend = WandbBackend(project="my-project", entity="my-team",
                       name="run-1", tags=["transformer", "baseline"])

# 传入已有 run
import wandb
run = wandb.init(project="my-project")
backend = WandbBackend(run=run)
```

行为：
- metric 帧 → `wandb.log(scalars, step=step)`
- config 帧 → `wandb.config.update(...)`
- event 帧  → `wandb.log({"event": msg}, step=step)`

---

## TensorBoardBackend

需要 `pip install tensorboard`（或 PyTorch 自带）。

```python
from exp_logger.components import TensorBoardBackend

backend = TensorBoardBackend(log_dir="runs/tb/run-1")

# 传入已有 writer
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter("runs/tb/run-1")
backend = TensorBoardBackend(writer=writer)
```

---

## TUIDashboard

需要 `pip install rich`。

```python
from exp_logger.components import TUIDashboard

# 作为 Backend 使用（自动在第一次 write 时启动线程）
dashboard = TUIDashboard(name="my-run", fps=6)

# 直接用于回放
dash = TUIDashboard(name="run [replay]", replay_speed=8)
dash.start()
for frame in frames:
    dash.push(frame)
    time.sleep(0.01)
dash.stop()
```

参数：

| 参数          | 类型           | 默认   |
|-------------|---------------|--------|
| name        | str           | "exp"  |
| fps         | int           | 6      |
| replay_speed| float \| None | None   |

自动展示规则：
- 前 4 个遇到的 numeric key → 顶部 4 个 metric 卡片 + sparkline
- 其余 numeric key → "All Metrics" 面板（每行一个 + sparkline）
- config dict → Config 面板（右侧）
- event strings → Event Feed（底部）

---

## ExpLogger（组装器）

```python
from exp_logger.components import ExpLogger, JSONLBackend, TUIDashboard, WandbBackend

# 手动组装
logger = ExpLogger(
    name="run-1",
    backends=[
        JSONLBackend("runs/run-1.jsonl"),
        WandbBackend(project="my-project"),
        TUIDashboard(),
    ]
)

# 从 config dict 自动组装（见 recipes.md）
logger = ExpLogger.from_config(cfg)
```

方法：

| 方法                    | 说明                              |
|------------------------|-----------------------------------|
| `config(**kwargs)`     | 记录超参数                        |
| `log(step=n, **metrics)` | 记录标量指标                    |
| `event(msg)`           | 记录里程碑事件                    |
| `close()`              | 关闭所有 backend                  |
| `from_config(cfg)`     | 从配置字典自动组装（工厂方法）     |

支持 context manager：`with ExpLogger(...) as logger: ...`
