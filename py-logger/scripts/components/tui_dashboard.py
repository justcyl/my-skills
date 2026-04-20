"""
exp_logger/components/tui_dashboard.py
───────────────────────────────────────
Rich Live TUI dashboard（可选依赖：rich）。

独立后台线程运行，不阻塞训练循环。
接收 MetricFrame 后自动：
  - 前 4 个 scalar key → 顶部 4 卡片 + sparkline
  - 其余 scalar → "All Metrics" 面板（每行一个 + sparkline）
  - config dict → Config 面板
  - event log  → Event Feed

也可以作为独立 Backend 注册进 ExpLogger：

    logger = ExpLogger(
        name="run-1",
        backends=[JSONLBackend("runs/run.jsonl"), TUIDashboard()]
    )

或者直接用于回放：

    dash = TUIDashboard(name="run-1 [replay]")
    dash.start()
    for frame in frames:
        dash.push(frame)
        time.sleep(0.05)
    dash.stop()
"""

from __future__ import annotations

import queue
import threading
import time
from collections import deque
from typing import Any

from .base import Backend, MetricFrame

# ── palette ──────────────────────────────────────────────────────────────────
_CYAN    = "rgb(86,196,255)"
_BLUE    = "rgb(84,140,255)"
_MINT    = "rgb(94,234,173)"
_AMBER   = "rgb(255,196,88)"
_CORAL   = "rgb(255,124,108)"
_DIM     = "rgb(170,184,210)"
_MUTED   = "rgb(110,127,158)"
_TEXT    = "rgb(231,238,251)"
_BORDER  = "rgb(58,76,106)"
_SPARK   = " ▁▂▃▄▅▆▇█"


def _spark(values: list[float], width: int = 32) -> str:
    if not values:
        return "─" * width
    tail = values[-width:]
    lo, hi = min(tail), max(tail)
    span = hi - lo or 1.0
    return "".join(_SPARK[int((v - lo) / span * (len(_SPARK) - 1))] for v in tail)


# ── dashboard state ───────────────────────────────────────────────────────────

class _State:
    def __init__(self, name: str):
        self.name    = name
        self.step    = 0
        self.t0      = time.time()
        self.status  = "waiting"
        self.config: dict[str, Any] = {}
        self.scalars: dict[str, float] = {}
        self.history: dict[str, deque] = {}
        self.events:  deque[str] = deque(maxlen=12)
        self._primary: list[str] = []       # first 4 numeric keys seen

    def update(self, frame: MetricFrame) -> None:
        t = frame.get("_type", "metric")
        if t == "init":
            self.t0 = frame.get("t", self.t0)
        elif t == "config":
            self.config.update({k: v for k, v in frame.items() if not k.startswith("_") and k != "t"})
            self.status = "running"
        elif t == "metric":
            self.step   = frame.get("step", self.step)
            self.status = "running"
            for k, v in frame.items():
                if k.startswith("_") or k in ("step", "t"):
                    continue
                if isinstance(v, (int, float)):
                    self.scalars[k] = float(v)
                    if k not in self.history:
                        self.history[k] = deque(maxlen=200)
                    self.history[k].append(float(v))
            if not self._primary:
                self._primary = list(self.scalars)[:4]
        elif t == "event":
            self.events.appendleft(frame.get("msg", ""))
        elif t == "done":
            self.status = "done"

    def elapsed(self) -> float:
        return time.time() - self.t0


# ── renderer ─────────────────────────────────────────────────────────────────

def _render(st: _State, replay_speed: float | None = None):
    """Build the full Rich renderable for one frame."""
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    # header ──────────────────────────────────────────────────────────────────
    status_color = {
        "running": _CYAN, "done": _MINT, "waiting": _AMBER, "paused": _AMBER,
    }.get(st.status, _DIM)
    hdr = Text()
    hdr.append("● ", style=f"bold {_CYAN}")
    hdr.append(st.name, style=f"bold {_TEXT}")
    hdr.append(f"  step {st.step:>5}", style=_DIM)
    hdr.append(f"  {st.elapsed():.0f}s", style=_MUTED)
    if replay_speed:
        hdr.append(f"  [replay {replay_speed}x]", style=_AMBER)
    hdr.append(f"  [{status_color}]{st.status}[/]")
    header = Panel(Align.left(hdr), box=box.SIMPLE, padding=(0, 0))

    # primary metric cards ────────────────────────────────────────────────────
    cards = []
    for key in (st._primary or list(st.scalars)[:4]):
        val  = st.scalars.get(key)
        hist = list(st.history.get(key, []))
        val_s = (f"{val:.4f}" if val is not None and abs(val) < 1e4
                 else (f"{val:.3e}" if val is not None else "—"))
        tbl = Table.grid(padding=(0, 1))
        tbl.add_column(style=_MUTED, min_width=8)
        tbl.add_column(style=_DIM)
        tbl.add_row("", Text(val_s, style=f"bold {_TEXT}"))
        tbl.add_row("spark", Text(_spark(hist, 22), style=_BLUE))
        if hist:
            lo, hi = min(hist), max(hist)
            rng = (f"{lo:.4f} — {hi:.4f}" if abs(hi) < 1e4 else f"{lo:.2e} — {hi:.2e}")
            tbl.add_row("range", Text(rng, style=_DIM))
        cards.append(Panel(tbl, title=f"[bold {_CYAN}]{key}[/]",
                           border_style=_BORDER, box=box.ROUNDED, padding=(0, 1)))
    while len(cards) < 4:
        cards.append(Panel("", border_style=_BORDER, box=box.ROUNDED))
    cards_row = Columns(cards, equal=True, expand=True)

    # all metrics table ───────────────────────────────────────────────────────
    other = [k for k in st.scalars if k not in st._primary]
    mt = Table.grid(padding=(0, 2))
    mt.add_column(style=_MUTED, min_width=14)
    mt.add_column(style=_DIM, min_width=10)
    mt.add_column(min_width=32)
    for k in other[:10]:
        v  = st.scalars[k]
        vs = f"{v:.4f}" if abs(v) < 1e4 else f"{v:.3e}"
        mt.add_row(k, vs, Text(_spark(list(st.history.get(k, [])), 28), style=_BLUE))
    all_metrics_panel = Panel(
        mt if other else Text("No additional metrics.", style=_MUTED),
        title=f"[bold {_MINT}]All Metrics[/]",
        border_style=_BORDER, box=box.ROUNDED, padding=(0, 1),
    )

    # config panel ────────────────────────────────────────────────────────────
    ct = Table.grid(padding=(0, 2))
    ct.add_column(style=_MUTED, min_width=12)
    ct.add_column(style=_DIM)
    for k, v in list(st.config.items())[:8]:
        ct.add_row(str(k), str(v))
    if not st.config:
        ct.add_row("", Text("No config logged yet.", style=_MUTED))
    cfg_panel = Panel(ct, title=f"[bold {_AMBER}]Config[/]",
                      border_style=_BORDER, box=box.ROUNDED, padding=(0, 1))

    middle = Columns([all_metrics_panel, cfg_panel], expand=True)

    # event feed ──────────────────────────────────────────────────────────────
    ev = Text()
    for e in list(st.events)[:6]:
        ev.append("• ", style=_CYAN)
        ev.append(e + "\n", style=_DIM)
    if not st.events:
        ev.append("Waiting for events…", style=_MUTED)
    events_panel = Panel(ev, title=f"[bold {_CORAL}]Event Feed[/]",
                         border_style=_BORDER, box=box.ROUNDED, padding=(0, 1))

    return Group(header, cards_row, middle, events_panel)


# ── TUIDashboard ─────────────────────────────────────────────────────────────

class TUIDashboard(Backend):
    """
    Rich Live TUI dashboard，作为 Backend 使用或独立用于回放。

    作为 Backend：
        logger = ExpLogger(name="run", backends=[JSONLBackend(...), TUIDashboard()])

    用于回放：
        dash = TUIDashboard(name="run [replay]")
        dash.start()
        for frame in frames: dash.push(frame); time.sleep(delay)
        dash.stop()
    """

    def __init__(self, name: str = "exp", fps: int = 6, replay_speed: float | None = None):
        self._state  = _State(name)
        self._queue: queue.Queue[MetricFrame] = queue.Queue()
        self._fps    = fps
        self._speed  = replay_speed
        self._stop   = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = False

    # ── Backend interface ─────────────────────────────────────────────────────

    def write(self, frame: MetricFrame) -> None:
        """Called by ExpLogger on each frame."""
        if not self._started:
            self.start()
        self._queue.put(frame)

    def close(self) -> None:
        self.stop()

    # ── Standalone interface ──────────────────────────────────────────────────

    def push(self, frame: MetricFrame | dict) -> None:
        """Alias for write(); accepts plain dicts too."""
        self.write(MetricFrame(frame))

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, hold: float = 1.5) -> None:
        """Gracefully stop: finish rendering, hold final frame, then exit."""
        self._queue.put(MetricFrame({"_type": "done"}))
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    # ── background thread ─────────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            from rich.console import Console
            from rich.live import Live
        except ImportError:
            raise ImportError("TUIDashboard requires rich: pip install rich")

        console  = Console()
        interval = 1.0 / self._fps

        with Live(console=console, refresh_per_second=self._fps, screen=True) as live:
            while not self._stop.is_set():
                while True:
                    try:
                        frame = self._queue.get_nowait()
                        self._state.update(frame)
                    except queue.Empty:
                        break
                live.update(_render(self._state, self._speed))
                time.sleep(interval)
            # drain remaining frames + final render
            while True:
                try:
                    frame = self._queue.get_nowait()
                    self._state.update(frame)
                except queue.Empty:
                    break
            live.update(_render(self._state, self._speed))
            time.sleep(1.5)
