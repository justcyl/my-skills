---
name: tm
description: "Remote GPU server management via `tm` CLI. Use when user needs to: (1) execute commands on remote servers, (2) run GPU training/evaluation experiments, (3) sync code to servers, (4) check GPU availability, (5) manage background jobs on servers. All operations are stateless SSH calls — develop locally, execute remotely."
---

# Remote Server Management with `tm`

Use `tm` CLI (`/Users/chenyl/project/tm/tm`) for all remote server operations. Each command is a stateless SSH call — no persistent connections, no tmux. Jobs survive SSH disconnection and local shutdown.

## Rules

1. **Always sync before remote execution** — code is developed locally, never edited on the server.
2. **Always use `uv`** for Python — `uv sync`, `uv run python`. Never `pip install` or `conda`.
3. **Check GPUs before experiments** — `tm gpu <server> --free`. Reserve at least 2 GPUs for others when >2 available.
4. **Use `exec` for short tasks, `run`+`wait` for long tasks** — anything over a few minutes should be a background job.
5. **Subagents execute, main agent fixes** — subagents (haiku) never modify code; they only run and report errors back.

## Task Decision

```
Is the task quick (<2 min)?
├── Yes → tm exec server "command"
└── No  → tm run server job-name "command"
          tm wait server job-name        (with run_in_background=True)
```

## Workflows

### Debug cycle

```bash
tm sync ./project server23:~/project
tm exec server23 "cd ~/project && uv sync"
tm exec server23 "cd ~/project && uv run python test.py"
# error → fix locally → sync → re-run
```

### Single training run

```bash
tm sync ./project server23:~/project
GPUS=$(tm gpu server23 --free)             # e.g. "0,1"
tm run server23 train-v1 "cd ~/project && uv run python train.py" -g $GPUS
# then use Bash(run_in_background=True):
tm wait server23 train-v1
# Claude Code continues other work; TaskOutput retrieves result when done
```

### Parallel experiments (subagents)

```bash
tm sync ./project server23:~/project
tm run server23 exp-lr1 "cd ~/project && uv run python train.py --lr 1e-3" -g 0,1
tm run server23 exp-lr2 "cd ~/project && uv run python train.py --lr 1e-4" -g 2,3
```
Spawn subagents (haiku, `run_in_background=True`) each running `tm wait server23 exp-*`.
If a subagent reports an error: fix locally → `tm sync` → new `tm run`.

### Error handling flow

1. Subagent reports error with log output
2. Main agent analyzes traceback, fixes code locally
3. `tm sync ./project server23:~/project`
4. `tm run server23 train-v2 "..."` (new job name)
5. Spawn new subagent to wait

## Command Quick Reference

| Command | Purpose | Blocks? |
|---------|---------|---------|
| `tm exec <server> <cmd>` | Run short command | Yes |
| `tm run <server> <name> <cmd>` | Start background job | No |
| `tm wait <server> <name>` | Wait for job completion | Yes (use `run_in_background`) |
| `tm status <server> <name>` | Check job state | No |
| `tm logs <server> <name>` | View job output | No |
| `tm stop <server> <name>` | Kill a job | No |
| `tm jobs <server>` | List jobs | No |
| `tm sync <src> <server>:<dst>` | Rsync (respects .gitignore) | Yes |
| `tm gpu <server>` | GPU status | No |

For full command options and output formats, read [references/commands.md](references/commands.md).

## `tm wait` Failure Reasons

| reason | exit_code | meaning |
|--------|-----------|---------|
| `process_exited` | non-zero | Command failed — check logs for traceback |
| `oom_killed` | 137 | Out of memory — reduce batch size or use more GPUs |
| `user_stopped` | 9/143 | Stopped by `tm stop` |
| `process_disappeared` | -1 | Killed externally or server rebooted |
| `server_unreachable` | - | Cannot SSH after max retries |

## Notes

- Servers configured via `~/.ssh/config` — use SSH Host names directly
- Job metadata stored on server at `~/.remote-jobs/<job-name>/`
- `tm sync` auto-applies `.gitignore` rules via `--filter=':- .gitignore'`
- Job names: letters, numbers, underscore, dash, dot only
