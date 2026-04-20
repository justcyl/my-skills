#!/usr/bin/env python3
"""
exp_logger/replay.py — 从 JSONL 文件回放实验监控
────────────────────────────────────────────────────
用法：
    python replay.py <file.jsonl>
    python replay.py <file.jsonl> --speed 8
    python replay.py <file.jsonl> --speed 0   # 即时（无延迟）

原理：
    读取 JSONL 文件，按原始时间戳比例回放到 TUIDashboard。
    使用 --speed N 加速 N 倍。
"""

import argparse
import json
import sys
import time
from pathlib import Path

# 支持直接运行（不安装包）
sys.path.insert(0, str(Path(__file__).parent))
from components.tui_dashboard import TUIDashboard
from components.base import MetricFrame


def replay(path: Path, speed: float = 1.0) -> None:
    frames: list[MetricFrame] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    frames.append(MetricFrame(json.loads(line)))
                except json.JSONDecodeError:
                    pass

    if not frames:
        print("No frames found.", file=sys.stderr)
        return

    name = next(
        (fr.get("name", path.stem) for fr in frames if fr.get("_type") == "init"),
        path.stem,
    )

    dash = TUIDashboard(name=f"{name}  [replay {speed}x]", replay_speed=speed)
    dash.start()

    t0_wall = time.time()
    t0_log  = frames[0].get("t", t0_wall)

    for i, frame in enumerate(frames):
        if speed > 0 and i > 0:
            log_elapsed  = frame.get("t", t0_log) - t0_log
            target_wall  = log_elapsed / speed
            wall_elapsed = time.time() - t0_wall
            sleep_for    = target_wall - wall_elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
        dash.push(frame)

    time.sleep(3)
    dash.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay an exp-logger JSONL log file.")
    parser.add_argument("file",  type=Path, help="Path to .jsonl log file")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Replay speed multiplier (0 = instant, default 1.0)")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    replay(args.file, speed=args.speed)


if __name__ == "__main__":
    main()
