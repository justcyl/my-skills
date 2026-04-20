"""
exp_logger/components/backend_wandb.py
───────────────────────────────────────
wandb backend（可选依赖）。

安装：pip install wandb

配置：
    WandbBackend(project="my-project")
    WandbBackend(project="my-project", entity="my-team", name="run-1", tags=["transformer"])
    WandbBackend(run=wandb.init(...))   # 传入已有 run

metric 帧 → wandb.log(scalars, step=step)
config 帧 → wandb.config.update(...)
event 帧  → wandb.log({"event": msg}, step=step)
"""

from __future__ import annotations

from typing import Any

from .base import Backend, MetricFrame


class WandbBackend(Backend):
    def __init__(self, run=None, **init_kwargs: Any):
        """
        参数：
          run         — 传入已有 wandb.run；否则内部调用 wandb.init(**init_kwargs)
          **init_kwargs — 直接透传给 wandb.init()
        """
        try:
            import wandb  # type: ignore
            self._wandb = wandb
        except ImportError as e:
            raise ImportError("WandbBackend requires 'wandb': pip install wandb") from e

        self._run = run or self._wandb.init(**init_kwargs)

    def write(self, frame: MetricFrame) -> None:
        t = frame.get("_type", "metric")

        if t == "config":
            payload = {k: v for k, v in frame.items() if not k.startswith("_") and k != "t"}
            self._run.config.update(payload)

        elif t == "metric":
            step    = frame.get("step")
            payload = {
                k: v for k, v in frame.items()
                if not k.startswith("_") and k not in ("step", "t")
                and isinstance(v, (int, float))
            }
            self._run.log(payload, step=step)

        elif t == "event":
            step = frame.get("step")
            self._run.log({"event": frame.get("msg", "")}, step=step)

    def close(self) -> None:
        try:
            self._run.finish()
        except Exception:
            pass
