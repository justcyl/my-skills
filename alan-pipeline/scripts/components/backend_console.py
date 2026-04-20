"""
exp_logger/components/backend_console.py
─────────────────────────────────────────
Console backend with in-place updating.

TTY mode (interactive terminal):
  - Config and events print once (scroll).
  - Metrics render a fixed-height block that overwrites itself each step.
  - Block shows: header, key metrics with trend + best, elapsed time.
  - Agent-readable: plain key=value text, no progress bars or spinners.

Non-TTY mode (pipe / captured by pi --print):
  - Simple one-line-per-step output, fully parseable.

Configuration:
    ConsoleBackend()                          # auto-detect TTY
    ConsoleBackend(keys=["loss", "accuracy"]) # only these metrics
    ConsoleBackend(live=False)                # force simple mode
"""

from __future__ import annotations

import sys
import time
from typing import Sequence

from .base import Backend, MetricFrame

# Trend arrows
_UP   = "↑"
_DOWN = "↓"
_FLAT = "·"


class ConsoleBackend(Backend):
    def __init__(
        self,
        keys: Sequence[str] | None = None,
        live: bool | None = None,
        file=None,
    ):
        self._keys     = list(keys) if keys else []
        self._file     = file or sys.stdout
        self._live     = live if live is not None else self._file.isatty()
        self._t0       = time.time()
        self._name     = ""
        self._step     = 0
        self._best: dict[str, tuple[float, str]] = {}  # key -> (best_val, direction)
        self._prev: dict[str, float] = {}
        self._block_h  = 0  # lines written in last block render
        self._config: dict = {}
        self._directions: dict[str, str] = {}  # key -> "min"|"max" (auto-detected)

    def write(self, frame: MetricFrame) -> None:
        t = frame.get("_type", "metric")

        if t == "init":
            self._name = frame.get("name", "exp")
            self._t0   = frame.get("t", self._t0)

        elif t == "config":
            self._config = {k: v for k, v in frame.items()
                           if not k.startswith("_") and k != "t"}
            kv = "  ".join(f"{k}={v}" for k, v in self._config.items())
            self._print_scroll(f"[config]  {kv}")

        elif t == "metric":
            self._step = frame.get("step", self._step)
            scalars = {k: float(v) for k, v in frame.items()
                       if not k.startswith("_") and k not in ("step", "t")
                       and isinstance(v, (int, float))}

            # Auto-detect direction for each key (first two data points)
            for k, v in scalars.items():
                if k not in self._directions and k in self._prev:
                    self._directions[k] = "min" if k.endswith("loss") else "max"
                # Update best
                direction = self._directions.get(k, "min")
                if k not in self._best:
                    self._best[k] = (v, direction)
                else:
                    bv, bd = self._best[k]
                    if (direction == "min" and v < bv) or (direction == "max" and v > bv):
                        self._best[k] = (v, bd)

            if self._live:
                self._render_block(scalars)
            else:
                self._render_line(scalars)

            self._prev = scalars

        elif t == "event":
            msg = frame.get("msg", "")
            if self._live and self._block_h > 0:
                self._clear_block()
            self._print_scroll(f"[event]  {msg}")
            self._block_h = 0

        elif t == "done":
            elapsed = frame.get("elapsed", time.time() - self._t0)
            if self._live and self._block_h > 0:
                # Print final block as scrolling text so it persists
                self._clear_block()
            self._print_scroll(f"[done]   {elapsed:.1f}s  step {self._step}")

    def close(self) -> None:
        pass

    # ── Non-TTY: simple one-line output ──────────────────────────────────

    def _render_line(self, scalars: dict[str, float]) -> None:
        ts = f"{time.time() - self._t0:5.0f}s"
        display = self._pick_keys(scalars)
        kv = "  ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                       for k, v in display.items())
        print(f"[{ts}] step {self._step:>5}  {kv}", file=self._file, flush=True)

    # ── TTY: in-place updating block ─────────────────────────────────────

    def _render_block(self, scalars: dict[str, float]) -> None:
        elapsed = time.time() - self._t0
        display = self._pick_keys(scalars)

        lines = []
        # Header
        header = f"── {self._name} ── step {self._step} ── {elapsed:.1f}s "
        header += "─" * max(0, 48 - len(header))
        lines.append(header)

        # Metric rows
        for k, v in display.items():
            vf = f"{v:.4f}" if abs(v) < 1e4 else f"{v:.3e}"

            # Trend
            trend = _FLAT
            if k in self._prev:
                diff = v - self._prev[k]
                if abs(diff) > 1e-8:
                    trend = _DOWN if diff < 0 else _UP

            # Best
            best_str = ""
            if k in self._best:
                bv, _ = self._best[k]
                bf = f"{bv:.4f}" if abs(bv) < 1e4 else f"{bv:.3e}"
                marker = " *" if abs(v - bv) < 1e-8 else ""
                best_str = f"  best {bf}{marker}"

            lines.append(f"  {k:<14} {vf:>10}  {trend}{best_str}")

        # Footer
        lines.append("─" * 48)

        # Move cursor up to overwrite previous block
        if self._block_h > 0:
            self._file.write(f"\033[{self._block_h}F")

        for line in lines:
            self._file.write(f"\033[K{line}\n")
        self._file.flush()

        self._block_h = len(lines)

    def _clear_block(self) -> None:
        """Clear the in-place block before printing scrolling text."""
        if self._block_h > 0:
            self._file.write(f"\033[{self._block_h}F")
            for _ in range(self._block_h):
                self._file.write("\033[K\n")
            self._file.write(f"\033[{self._block_h}F")
            self._file.flush()
            self._block_h = 0

    # ── helpers ──────────────────────────────────────────────────────────

    def _pick_keys(self, scalars: dict[str, float]) -> dict[str, float]:
        if self._keys:
            return {k: scalars[k] for k in self._keys if k in scalars}
        return scalars

    def _print_scroll(self, text: str) -> None:
        print(text, file=self._file, flush=True)
