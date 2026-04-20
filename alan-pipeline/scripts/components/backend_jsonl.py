"""
exp_logger/components/backend_jsonl.py
───────────────────────────────────────
JSONL 文件 backend。

每帧追加一行 JSON，行缓冲（buffering=1）保证进程崩溃也不丢数据。
这个 backend 是回放功能的数据源，建议始终开启。

配置：
    JSONLBackend(path="runs/exp.jsonl")
    JSONLBackend(path=Path("runs") / "exp.jsonl")
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from .base import Backend, MetricFrame


class JSONLBackend(Backend):
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self._path, "a", buffering=1)
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    def write(self, frame: MetricFrame) -> None:
        line = json.dumps(dict(frame)) + "\n"
        with self._lock:
            self._file.write(line)

    def close(self) -> None:
        with self._lock:
            if not self._file.closed:
                self._file.close()
