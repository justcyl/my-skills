# exp-logger

- skill_id: `py-logger`
- status: `managed`
- skill_path: `py-logger`
- source_type: `local-manual`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

为 Python 训练程序提供可组合的实验日志与 TUI 监控组件库。
当用户需要训练日志、实验可视化、TUI dashboard、TUI 指标回放、
wandb 或 tensorboard 集成时使用。
触发语境：「做个训练 logger」「给我写个实验日志系统」「加个 wandb 集成」
「训练过程可视化」「dashboard 监控训练」「实验回放」「TUI 监控」。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `py-logger/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
