#!/usr/bin/env python3
"""
exp_logger/watch.py — real-time TUI monitor for a growing JSONL file.
────────────────────────────────────────────────────────────────────────
Usage:
    python watch.py <file.jsonl>
    python watch.py <file.jsonl> --poll 0.2     # poll interval (default 0.3s)

Design:
    Training code writes JSONL to disk (JSONLBackend).
    This script runs in a SEPARATE terminal, tails the file,
    and renders a live TUI dashboard from the growing data.

    Training code never imports Rich or any display library.
    This script is the only place display logic lives.

Example workflow:
    # Terminal 1: train
    python train.py

    # Terminal 2: watch (start before, during, or after training)
    python watch.py runs/exp.jsonl
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from components.tui_dashboard import TUIDashboard
from components.base import MetricFrame


def watch(path: Path, poll: float = 0.3) -> None:
    """Tail a JSONL file and feed frames into TUIDashboard in real time."""

    # Wait for file to appear
    waited = 0.0
    while not path.exists():
        if waited == 0:
            print(f"Waiting for {path} ...", file=sys.stderr)
        time.sleep(poll)
        waited += poll
        if waited > 300:
            print(f"Timed out waiting for {path}", file=sys.stderr)
            sys.exit(1)

    name = path.stem
    dash = TUIDashboard(name=name)
    dash.start()

    with open(path) as f:
        done = False
        idle_count = 0
        while not done:
            line = f.readline()
            if line:
                line = line.strip()
                if not line:
                    continue
                idle_count = 0
                try:
                    frame = MetricFrame(json.loads(line))
                    dash.push(frame)
                    # Detect init frame for name
                    if frame.get("_type") == "init" and "name" in frame:
                        name = frame["name"]
                        dash._state.name = name
                    # Detect done frame
                    if frame.get("_type") == "done":
                        done = True
                except json.JSONDecodeError:
                    pass
            else:
                idle_count += 1
                time.sleep(poll)
                # After 10 minutes of no data, auto-exit
                if idle_count * poll > 600:
                    done = True

    # Hold final frame for a moment
    time.sleep(2)
    dash.stop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch a growing JSONL file and display a live TUI dashboard.")
    parser.add_argument("file", type=Path, help="Path to .jsonl log file")
    parser.add_argument("--poll", type=float, default=0.3,
                        help="File poll interval in seconds (default 0.3)")
    args = parser.parse_args()
    watch(args.file, poll=args.poll)


if __name__ == "__main__":
    main()
