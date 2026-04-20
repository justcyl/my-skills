"""
exp_logger/components/backend_tensorboard.py
─────────────────────────────────────────────
TensorBoard backend（可选依赖）。

安装：pip install tensorboard   （或 torch.utils.tensorboard）

配置：
    TensorBoardBackend(log_dir="runs/tb/run-1")
    TensorBoardBackend(writer=SummaryWriter(...))  # 传入已有 writer

metric 帧 → writer.add_scalar(key, value, global_step)
config 帧 → writer.add_text("config", str(payload), 0)
event 帧  → writer.add_text("event", msg, step)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Backend, MetricFrame


class TensorBoardBackend(Backend):
    def __init__(self, log_dir: str | Path | None = None, writer=None):
        """
        参数：
          log_dir — TensorBoard 日志目录；若传入 writer 则忽略
          writer  — 传入已有 SummaryWriter
        """
        if writer is not None:
            self._writer = writer
        else:
            try:
                from torch.utils.tensorboard import SummaryWriter  # type: ignore
            except ImportError:
                try:
                    from tensorboard.summary.writer.event_file_writer import EventFileWriter  # type: ignore
                    from torch.utils.tensorboard import SummaryWriter  # type: ignore
                except ImportError:
                    raise ImportError(
                        "TensorBoardBackend requires tensorboard: pip install tensorboard"
                    )
            self._writer = SummaryWriter(log_dir=str(log_dir or "runs/tb"))

    def write(self, frame: MetricFrame) -> None:
        t = frame.get("_type", "metric")

        if t == "config":
            payload = {k: v for k, v in frame.items() if not k.startswith("_") and k != "t"}
            self._writer.add_text("config", str(payload), global_step=0)

        elif t == "metric":
            step = frame.get("step", 0)
            for k, v in frame.items():
                if not k.startswith("_") and k not in ("step", "t") and isinstance(v, (int, float)):
                    self._writer.add_scalar(k, v, global_step=step)

        elif t == "event":
            step = frame.get("step", 0)
            self._writer.add_text("event", frame.get("msg", ""), global_step=step)

    def close(self) -> None:
        try:
            self._writer.close()
        except Exception:
            pass
