"""
exp_logger/components/__init__.py
──────────────────────────────────
公开组件库的全部可组合部件。

from exp_logger.components import (
    MetricFrame,
    Backend,
    JSONLBackend,
    ConsoleBackend,
    WandbBackend,          # 需要 pip install wandb
    TensorBoardBackend,    # 需要 pip install tensorboard
    TUIDashboard,          # 需要 pip install rich
    ExpLogger,
)
"""

from .base                   import MetricFrame, Backend
from .backend_jsonl          import JSONLBackend
from .backend_console        import ConsoleBackend
from .backend_wandb          import WandbBackend
from .backend_tensorboard    import TensorBoardBackend
from .tui_dashboard          import TUIDashboard
from .logger                 import ExpLogger

__all__ = [
    "MetricFrame",
    "Backend",
    "JSONLBackend",
    "ConsoleBackend",
    "WandbBackend",
    "TensorBoardBackend",
    "TUIDashboard",
    "ExpLogger",
]
