# ph-paper-helper

- skill_id: `ph-paper-helper`
- status: `managed`
- skill_path: `ph-paper-helper`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `passed`

## Summary

使用 paper-helper (ph) CLI 进行学术论文检索与渐进式阅读。当 agent 需要查找论文、了解某研究领域的现状、获取论文摘要或精读全文时使用。覆盖完整工作流：初始化 workspace → 搜索 → L1 摘要筛选 → 按需获取 L2 全文。适用场景包括"帮我找关于 X 的论文"、"调研 Y 方向的工作"、"精读这篇论文"、"搜索 Z 作者的研究"。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `ph-paper-helper/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
