"""
exp_logger/components/logger.py
────────────────────────────────
ExpLogger — 组装器。把任意 Backend 列表串联在一起。

设计原则：
  - Logger 只负责组装与路由，不包含任何显示逻辑
  - 所有行为由传入的 backends 决定
  - 内置便捷工厂方法 from_config() 适合 argparse / config dict 场景

典型用法：

    # 最简单：只写 JSONL
    logger = ExpLogger(name="run", backends=[JSONLBackend("runs/run.jsonl")])

    # 带 TUI
    from exp_logger.components import JSONLBackend, TUIDashboard
    logger = ExpLogger(name="run", backends=[
        JSONLBackend("runs/run.jsonl"),
        TUIDashboard(),
    ])

    # 带 wandb
    from exp_logger.components import JSONLBackend, TUIDashboard, WandbBackend
    logger = ExpLogger(name="run", backends=[
        JSONLBackend("runs/run.jsonl"),
        WandbBackend(project="my-project"),
        TUIDashboard(),
    ])

    # 从 config dict 自动组装（适合 argparse）
    logger = ExpLogger.from_config(cfg)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Sequence

from .base import Backend, MetricFrame


class ExpLogger:
    """组装多个 Backend，提供统一的日志接口。"""

    def __init__(self, name: str, backends: Sequence[Backend]):
        self.name      = name
        self._backends = list(backends)
        self._step     = 0
        self._t0       = time.time()
        self._closed   = False
        # broadcast init frame
        self._broadcast(MetricFrame({"_type": "init", "name": name, "t": self._t0}))

    # ── public API ────────────────────────────────────────────────────────────

    def config(self, **kwargs: Any) -> None:
        """记录超参数 / 配置（通常在训练开始前调用一次）。"""
        self._broadcast(MetricFrame.config(**kwargs))

    def log(self, step: int | None = None, **metrics: Any) -> None:
        """记录一步的标量指标。"""
        if step is not None:
            self._step = step
        self._broadcast(MetricFrame.metric(self._step, **metrics))

    def event(self, msg: str) -> None:
        """记录里程碑事件（checkpoint、phase change 等）。"""
        self._broadcast(MetricFrame.event(self._step, msg))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._broadcast(MetricFrame.done(self._step, time.time() - self._t0))
        for b in self._backends:
            try:
                b.close()
            except Exception as e:
                print(f"[exp_logger] backend close error: {e}", file=sys.stderr)

    # context manager
    def __enter__(self) -> "ExpLogger":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ── factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_config(cls, cfg: dict) -> "ExpLogger":
        """
        从配置字典自动组装 backends。

        cfg 支持字段：
          name       str           实验名称
          logdir     str           JSONL 文件目录（默认 "runs"）
          tui        bool|"auto"   是否开启 TUI（"auto" = tty 检测）
          wandb      dict|None     传给 WandbBackend 的参数
          tensorboard str|None     TensorBoard log_dir
          console    str           "full"|"compact"|"silent"（默认 "full"）
          console_keys list[str]   compact 模式要显示的 keys

        示例：
          cfg = {"name": "run-1", "logdir": "runs", "tui": "auto",
                 "wandb": {"project": "my-proj"}}
          logger = ExpLogger.from_config(cfg)
        """
        name    = cfg.get("name", "exp")
        logdir  = cfg.get("logdir", "runs")
        backends: list[Backend] = []

        # ── JSONL（始终开启）─────────────────────────────────────────────────
        from .backend_jsonl import JSONLBackend
        ts   = time.strftime("%Y%m%d_%H%M%S")
        path = Path(logdir) / f"{name}_{ts}.jsonl"
        jb   = JSONLBackend(path)
        backends.append(jb)

        # ── wandb ─────────────────────────────────────────────────────────────
        if cfg.get("wandb"):
            from .backend_wandb import WandbBackend
            backends.append(WandbBackend(**cfg["wandb"]))

        # ── TensorBoard ───────────────────────────────────────────────────────
        if cfg.get("tensorboard"):
            from .backend_tensorboard import TensorBoardBackend
            backends.append(TensorBoardBackend(log_dir=cfg["tensorboard"]))

        # ── TUI vs Console ────────────────────────────────────────────────────
        tui_setting = cfg.get("tui", "auto")
        show_tui    = tui_setting is True or (tui_setting == "auto" and sys.stdout.isatty())

        if show_tui:
            from .tui_dashboard import TUIDashboard
            backends.append(TUIDashboard(name=name))
        else:
            from .backend_console import ConsoleBackend
            backends.append(ConsoleBackend(
                verbose=cfg.get("console", "full"),
                keys=cfg.get("console_keys"),
            ))

        logger = cls(name=name, backends=backends)
        # expose JSONL path as convenience attribute
        logger.log_path = jb.path
        return logger

    # ── internals ─────────────────────────────────────────────────────────────

    def _broadcast(self, frame: MetricFrame) -> None:
        for b in self._backends:
            try:
                b.write(frame)
            except Exception as e:
                print(f"[exp_logger] backend write error ({type(b).__name__}): {e}",
                      file=sys.stderr)
