# pi-tmux

- skill_id: `pi-tmux`
- status: `managed`
- skill_path: `pi-tmux`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

指导 agent 正确使用 pi-tmux 扩展管理后台 tmux 进程。涵盖 run/peek/send/kill/list 五个 action 的使用时机与参数选择、silenceTimeout 与 watchInterval 的配置策略、completion/silence/watchdog 三种自动通知的响应方式，以及常见工作流模式（dev server、build、交互式程序、长时间训练）。适用于 agent 需要在后台运行命令、监控进程输出、与交互式程序通信时。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pi-tmux/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
