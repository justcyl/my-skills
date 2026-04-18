"""
exp_logger/components/backend_console.py
─────────────────────────────────────────
纯文本 console backend。

在没有 TUI 时提供可读的 stdout 输出。
支持三种详细程度：

  verbose="full"    每一步都打印所有字段（默认）
  verbose="compact" 每一步打印 step + 指定 keys
  verbose="silent"  只打印 event / done，不打印 metric

配置：
    ConsoleBackend()
    ConsoleBackend(verbose="compact", keys=["loss", "accuracy"])
    ConsoleBackend(verbose="silent")
"""

from __future__ import annotations

import sys
import time
from typing import Literal, Sequence

from .base import Backend, MetricFrame


class ConsoleBackend(Backend):
    def __init__(
        self,
        verbose: Literal["full", "compact", "silent"] = "full",
        keys: Sequence[str] | None = None,
        file=None,
    ):
        self._verbose = verbose
        self._keys    = list(keys) if keys else []
        self._file    = file or sys.stdout
        self._t0      = time.time()

    def write(self, frame: MetricFrame) -> None:
        t  = frame.get("_type", "metric")
        ts = f"{time.time() - self._t0:6.0f}s"

        if t == "config":
            kv = "  ".join(
                f"{k}={v}" for k, v in frame.items()
                if not k.startswith("_") and k != "t"
            )
            print(f"[config]  {kv}", file=self._file, flush=True)

        elif t == "metric":
            if self._verbose == "silent":
                return
            step = frame.get("step", "?")
            if self._verbose == "compact" and self._keys:
                kv = "  ".join(
                    f"{k}={frame[k]:.4f}" if isinstance(frame.get(k), float) else f"{k}={frame.get(k, '—')}"
                    for k in self._keys
                )
            else:
                kv = "  ".join(
                    f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                    for k, v in frame.items()
                    if not k.startswith("_") and k not in ("step", "t")
                )
            print(f"[{ts}] step {step:>5}  {kv}", file=self._file, flush=True)

        elif t == "event":
            step = frame.get("step", "?")
            msg  = frame.get("msg", "")
            print(f"[event]   step {step:>5}  {msg}", file=self._file, flush=True)

        elif t == "done":
            elapsed = frame.get("elapsed", time.time() - self._t0)
            print(f"[done]    elapsed {elapsed:.0f}s", file=self._file, flush=True)

    def close(self) -> None:
        pass
