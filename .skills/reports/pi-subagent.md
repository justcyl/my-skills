# pi-subagent

- skill_id: `pi-subagent`
- status: `managed`
- skill_path: `pi-subagent`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

通用 pi sub-agent 基础设施。把 pi + herdr 创建 sub-agent 的模式抽象为可复用组件：模型路由表（alias → 实际模型 + 参数）、agent 目录（每种能力一个 system prompt md）、通用 invoke.sh。其他 skill 或 agent 直接引用 invoke.sh 和 agent 目录来调度 sub-agent，无需为每种能力单独维护一套 invoke 脚本。触发场景：'创建 sub-agent'、'用 pi 跑个子任务'、'需要调用 gemini 做 X'、'spawn a sub-agent'。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `pi-subagent/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
