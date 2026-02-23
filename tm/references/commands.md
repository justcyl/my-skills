# tm Command Reference

Complete options and output formats for all `tm` commands.

## tm exec

```
tm exec <server> <command> [-t|--timeout <sec>] [-d|--workdir <path>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-t, --timeout` | 120 | Timeout in seconds |
| `-d, --workdir` | ~ | Remote working directory |

Output:
```
[stdout/stderr of command]
--- EXIT CODE: 0 ---
```

Exit code matches remote command's exit code. 124 = timeout.

## tm run

```
tm run <server> <job-name> <command> [-d|--workdir <path>] [-g|--gpus <ids>] [-e|--env <K=V>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-d, --workdir` | ~ | Remote working directory |
| `-g, --gpus` | - | CUDA_VISIBLE_DEVICES |
| `-e, --env` | - | Environment variable (repeatable) |

Output (success):
```
JOB_STARTED
server: gpu-server-23
job: train-v1
pid: 45678
log: ~/.remote-jobs/train-v1/output.log
started_at: 2026-02-13T14:30:00
```

Output (conflict):
```
ERROR: job 'train-v1' is already running on gpu-server-23 (pid: 45678)
Use 'tm stop server23 train-v1' to stop it first.
```

Job name constraints: `[a-zA-Z0-9_.-]+`

## tm wait

```
tm wait <server> <job-name> [--tail <lines>] [--max-retries <n>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--tail` | 50 | Log lines to show on completion |
| `--max-retries` | 10 | SSH reconnection attempts |

Polling: 5s (first 2min) → 15s (2-10min) → 30s (after 10min). Auto-reconnects with exponential backoff on SSH failure.

Output (success):
```
JOB_COMPLETED
job:            train-v1
exit_code:      0
elapsed:        02:15:30
--- LAST 50 LINES ---
[log content]
```

Output (failure):
```
JOB_FAILED
job:            train-v1
exit_code:      137
elapsed:        00:45:12
reason:         oom_killed
hint:           Process killed by OOM Killer. Consider reducing batch size or using more GPUs.
--- LAST 50 LINES ---
[log content]
```

Exit code matches the job's exit code.

## tm status

```
tm status <server> <job-name>
```

Output:
```
JOB_STATUS
job:            train-v1
state:          running
pid:            45678
elapsed:        01:23:45
exit_code:      -
```

State values: `running`, `done`, `failed`.

## tm logs

```
tm logs <server> <job-name> [--tail <lines>] [--all]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--tail` | 50 | Last N lines |
| `--all` | false | Full log |

Output: raw log content.

## tm stop

```
tm stop <server> <job-name> [-f|--force]
```

Default: SIGTERM, wait 5s, then SIGKILL. `--force`: immediate SIGKILL.

Output:
```
JOB_STOPPED
job:            train-v1
pid:            45678
signal:         SIGTERM
```

## tm jobs

```
tm jobs <server> [--all] [--json]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--all` | false | Include completed/failed jobs |
| `--json` | false | JSON output |

Output (table):
```
JOB                  STATE      PID      ELAPSED      EXIT
train-v1             running    45678    01:23:45     -
eval-1               done       45679    00:15:30     0
```

Default: running jobs only. `--all` includes completed/failed.

## tm sync

```
tm sync [rsync-options] <source> <server>:<dest> [-w|--watch] [--no-gitignore]
```

| Option | Description |
|--------|-------------|
| `-w, --watch` | Watch for changes, auto-sync |
| `--no-gitignore` | Don't apply .gitignore filter |
| All other options | Passed directly to rsync |

Auto-applies `--filter=':- .gitignore'` unless `--no-gitignore`. All standard rsync flags work: `--delete`, `-n` (dry-run), `--exclude`, etc.

Output (one-shot):
```
[rsync output]
SYNC_COMPLETE
```

Output (watch):
```
WATCHING ./project -> server23:~/project
[2026-02-13 14:30:05] synced
[2026-02-13 14:31:12] synced
```

Watch mode requires `fswatch` (macOS) or `inotifywait` (Linux).

## tm gpu

```
tm gpu <server> [--free] [--json]
```

| Option | Description |
|--------|-------------|
| `--free` | Output only available GPU IDs (memory <10%), comma-separated |
| `--json` | JSON output |

Output (table):
```
GPU   NAME                   MEMORY                   UTIL   STATUS
0     A100-SXM4-80GB         1.2/80.0 GB (1%)         0%     available
1     A100-SXM4-80GB         0.0/80.0 GB (0%)         0%     available
2     A100-SXM4-80GB         45.3/80.0 GB (57%)       89%    moderate
3     A100-SXM4-80GB         78.1/80.0 GB (98%)       99%    busy
```

Output (`--free`):
```
0,1
```

Status thresholds: <10% available, <50% light, <90% moderate, >=90% busy.
