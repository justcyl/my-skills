# wandb 深度集成

## 基础用法

```python
from exp_logger.components import WandbBackend

backend = WandbBackend(project="my-project")
```

`WandbBackend(**init_kwargs)` 的参数直接透传给 `wandb.init()`。完整参数见 [wandb 文档](https://docs.wandb.ai/ref/python/init)。

常用参数：

```python
WandbBackend(
    project  = "my-project",    # 必填
    entity   = "my-team",       # 可选
    name     = "run-1",         # run 名称
    tags     = ["transformer", "baseline"],
    config   = {"lr": 3e-4},    # 也可以用 logger.config(**kwargs)
    group    = "sweep-01",
    notes    = "first ablation",
    mode     = "online",        # "online" | "offline" | "disabled"
    dir      = "wandb-runs",    # 本地存储目录
)
```

## 复用已有 run

```python
import wandb
run = wandb.init(project="my-project", resume="allow")
backend = WandbBackend(run=run)
```

## sweep 集成

wandb sweep 会通过 `wandb.config` 注入超参数。在 sweep agent 函数里：

```python
import wandb
from exp_logger.components import ExpLogger, JSONLBackend, WandbBackend, TUIDashboard

def train():
    # wandb sweep 已经调用了 wandb.init()
    run = wandb.run
    cfg = dict(run.config)     # 获取 sweep 注入的超参

    logger = ExpLogger(
        name=run.name,
        backends=[
            JSONLBackend(f"runs/{run.name}.jsonl"),
            WandbBackend(run=run),      # 传入已有 run，避免重复 init
            TUIDashboard(name=run.name),
        ]
    )
    logger.config(**cfg)

    for step in range(1000):
        loss = train_step(**cfg)
        logger.log(step=step, loss=loss)

    logger.close()

wandb.agent(sweep_id, train)
```

## 离线模式（无网络环境）

```python
WandbBackend(project="my-project", mode="offline")
# 之后在有网时同步：
# wandb sync wandb/offline-run-*
```

## 关闭 wandb（调试时不想上传）

```python
WandbBackend(project="my-project", mode="disabled")
# 或者直接不添加 WandbBackend 到 backends 列表
```

## from_config 中使用 wandb

```python
cfg = {
    "name": "run-1",
    "logdir": "runs",
    "tui": "auto",
    "wandb": {
        "project": "my-project",
        "entity": "my-team",
        "tags": ["v2", "ablation"],
    }
}
logger = ExpLogger.from_config(cfg)
```

`from_config` 会把 `cfg["wandb"]` 整个传给 `WandbBackend(**cfg["wandb"])`。

## MetricFrame 与 wandb 的映射

| MetricFrame._type | wandb 行为                             |
|------------------|-----------------------------------------|
| config           | `run.config.update(payload)`           |
| metric           | `run.log(scalars, step=step)`          |
| event            | `run.log({"event": msg}, step=step)`   |
| init / done      | 忽略                                   |

非 scalar 字段（list、dict）不会被上传（wandb 不支持直接 log）。
如需上传图像、表格等复杂类型，自定义 `WandbBackend.write()` 的逻辑。
