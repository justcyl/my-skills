---
name: pi-tmux
description: 指导 agent 正确使用 pi-tmux 扩展管理后台 tmux 进程。涵盖 run/peek/send/kill/list 五个 action 的使用时机与参数选择、silenceTimeout 与 watchInterval 的配置策略、completion/silence/watchdog 三种自动通知的响应方式，以及常见工作流模式（dev server、build、交互式程序、长时间训练）。适用于 agent 需要在后台运行命令、监控进程输出、与交互式程序通信时。
---

# pi-tmux

pi-tmux 是一个 pi 扩展，提供 `tmux` tool，将长时间运行的命令放到后台 tmux window 中。命令完成、进程安静、定时快照三种场景会自动向对话注入通知。

## When To Use

**用 tmux run**（而不是 bash）的场景：
- Dev server（`npm run dev`, `python manage.py runserver`）
- Build / compile（`cargo build`, `make -j8`）
- Test suite（`pytest`, `npm test`，尤其是可能跑几分钟以上的）
- File watcher（`tsc --watch`, `nodemon`）
- 训练任务（`python train.py`）
- 任何预期超过 10 秒的命令

**继续用 bash** 的场景：
- 快速查询命令（`ls`, `cat`, `grep`, `git status`, `git diff`）
- 一次性修改命令（`git commit`, `npm install`, `mkdir`）
- 预期秒级完成的短命令

**判断标准**：如果你不确定命令要跑多久，默认用 bash。只有明确知道会长时间运行时才用 tmux。

## Tool API Quick Reference

```
tmux run    command="npm run dev" name="dev-server" [cwd] [silenceTimeout] [watchInterval]
tmux peek   [window="dev-server" | window="all"]
tmux send   window="dev-server" [text="Y"] [keys="Enter"]
tmux kill   window="dev-server"
tmux list
```

## Core Principles

### 1. Run 之后立刻继续工作

`tmux run` 是非阻塞的。发出 run 后，**不要等待输出**，立刻做下一件事。命令完成后你会自动收到 `tmux-completion` 通知。

### 2. 给每个 window 起语义化的 name

```
✓ name="dev-server"     name="test-suite"     name="build"
✗ 不提供 name（自动从命令提取，不够清晰）
```

之后所有操作（peek/send/kill）都用 name 引用 window，不要用 index。

### 3. 不要主动轮询——等通知

三种通知会自动来：
- **tmux-completion**：命令退出（带 exit code + 最后 20 行输出）→ **需要你响应**
- **tmux-silence**：窗口安静超过阈值 → **需要你响应**（可能在等 input）
- **tmux-watchdog**：定时快照 → **仅供参考**，不需要响应

收到 completion 通知后，根据 exit code 判断下一步：
- exit 0 → 成功，继续后续任务
- exit 非 0 → peek 查看完整输出，诊断问题

## Parameter Strategy

### silenceTimeout

**什么时候用**：命令可能弹出交互式提示（Y/n、密码、确认）时。

```
tmux run command="npm init" name="init" silenceTimeout=10
```

收到 silence 通知后的决策树：

1. **peek** 查看输出
2. 如果是简单提示（Y/n, Enter to continue）→ **send** 回复
3. 如果是复杂交互（多步向导、需要大量输入）→ **kill** 并用非交互方式重跑
4. 如果只是命令运行慢（还在产出但偶尔停顿）→ 忽略，silence 会自动退避

**不需要用的场景**：`npm run dev`、`cargo build` 等不会提示交互的命令。

### watchInterval

**什么时候用**：长时间任务，你想看中间进度但不想手动 peek。

```
tmux run command="python train.py --epochs 100" name="training" watchInterval=60
```

典型值：
- Build（1-5 分钟）：`watchInterval=30`
- 训练任务（几十分钟）：`watchInterval=60`
- 不需要中间状态的：不设

## Workflow Patterns

### Pattern 1: Dev Server

```
tmux run command="npm run dev" name="dev-server"
→ 继续编辑代码
→ 需要看输出时: tmux peek window="dev-server"
→ 不再需要时: tmux kill window="dev-server"
```

Dev server 通常不会退出，所以不需要 silenceTimeout 也不需要 watchInterval。

### Pattern 2: Build + 后续任务

```
tmux run command="cargo build --release" name="build" watchInterval=30
→ 继续做其他事
→ 收到 tmux-completion (exit 0) → 继续部署/测试
→ 收到 tmux-completion (exit 非 0) → peek 查看错误，修复代码
```

### Pattern 3: 可能需要交互的命令

```
tmux run command="npx create-next-app my-app" name="create-app" silenceTimeout=15
→ 收到 tmux-silence → peek
→ 看到 "Would you like to use TypeScript? (Y/n)"
→ tmux send window="create-app" text="Y" keys="Enter"
→ 等下一次 silence 或 completion
```

### Pattern 4: 并行多任务

```
tmux run command="npm run dev" name="dev-server"
tmux run command="npm test -- --watch" name="test-watch"
tmux run command="tsc --watch" name="type-check"
→ tmux list 查看所有窗口状态
→ tmux peek window="all" 一次看全部输出
```

### Pattern 5: 长时间训练

```
tmux run command="python train.py" name="training" watchInterval=60 silenceTimeout=120
→ 每 60 秒收到 watchdog 快照（不打断你）
→ 如果 120 秒无输出收到 silence 通知（可能卡了）
→ 训练结束收到 completion 通知
```

## Responding to Notifications

### tmux-completion（triggerTurn: true）

**你必须响应**。看到此通知时：

1. 检查 exit code
2. 如果成功，继续下一步工作流
3. 如果失败，peek 查看详细输出后诊断

### tmux-silence（triggerTurn: true）

**你必须响应**。看到此通知时：

1. peek 查看当前输出
2. 判断是否需要交互
3. send 回复 或 kill 重跑 或 忽略（silence 会自动退避）

### tmux-watchdog（triggerTurn: false）

**仅供参考**，不需要专门响应。快照会出现在对话历史中，当你后续做决策时可以参考。

## Anti-Patterns

❌ **run 之后立刻 peek** — 浪费一轮调用，等通知即可

❌ **用 bash 跑 dev server** — 会阻塞 agent

❌ **忘了 kill 不再需要的 window** — tmux list 检查，及时清理

❌ **对简单短命令用 tmux** — `git status` 不需要放后台

❌ **同一个 name 反复 run** — 先 kill 旧的再创建新的

❌ **设了 silenceTimeout 却不响应 silence 通知** — 这会让程序一直等

## Slash Commands (User-facing)

用户可以使用的斜杠命令：
- `/tmux` — 在新终端标签页 attach 到 session
- `/tmux:cat` — 选择一个 window，将输出注入对话
- `/tmux:clear` — 杀掉所有空闲 window
