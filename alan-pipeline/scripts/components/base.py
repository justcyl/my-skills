"""
exp_logger/components/base.py
─────────────────────────────
数据契约 + Backend 抽象基类。

所有 backend 只需继承 Backend 并实现 write(frame) 和 close()。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any


# ── 核心数据类型 ─────────────────────────────────────────────────────────────

class MetricFrame(dict):
    """
    一帧日志数据。本质是一个 dict，加了类型标记约定：

      _type : "init" | "config" | "metric" | "event" | "done"
      step  : int          （metric / event 帧）
      t     : float        （UTC epoch，由 ExpLogger 自动注入）
      ...   : 任意 scalar / string 字段

    不强制 schema，所有字段都是可选的。
    Backend 负责自行处理缺失字段。
    """

    @staticmethod
    def metric(step: int, **kwargs: Any) -> "MetricFrame":
        return MetricFrame({"_type": "metric", "step": step, "t": time.time(), **kwargs})

    @staticmethod
    def event(step: int, msg: str) -> "MetricFrame":
        return MetricFrame({"_type": "event", "step": step, "t": time.time(), "msg": msg})

    @staticmethod
    def config(**kwargs: Any) -> "MetricFrame":
        return MetricFrame({"_type": "config", "t": time.time(), **kwargs})

    @staticmethod
    def done(step: int, elapsed: float) -> "MetricFrame":
        return MetricFrame({"_type": "done", "step": step, "t": time.time(), "elapsed": elapsed})


# ── Backend ABC ───────────────────────────────────────────────────────────────

class Backend(ABC):
    """
    所有 backend 的统一接口。

    实现要求：
      - write(frame) 必须是线程安全的（ExpLogger 可能在多线程环境使用）
      - close() 必须幂等（允许多次调用）
    """

    @abstractmethod
    def write(self, frame: MetricFrame) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> "Backend":
        return self

    def __exit__(self, *_) -> None:
        self.close()
