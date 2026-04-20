# fair-experiment-tracker

- skill_id: `fair-experiment-tracker`
- status: `managed`
- skill_path: `fair-experiment-tracker`
- source_type: `local`
- source: `/var/folders/f7/qbcrpmf56n5bf47z0ndz_s_00000gn/T/tmp.9rS3AupK5h/skill/fair-experiment-tracker`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

基于 FAIR / Meta AI 风格实验管理方法论的实验追踪表格生成技能。
当用户需要设计实验追踪表格、管理机器学习/深度学习实验、记录和对比实验结果、建立对照组、系统化研究 workflow、创建 ablation study 表格，或提出“帮我管理实验”“我想系统化我的研究流程”“做个 research spreadsheet / 实验表格”等需求时，使用此技能。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `fair-experiment-tracker/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
