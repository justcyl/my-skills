# ph-paper-helper

- skill_id: `ph-paper-helper`
- status: `managed`
- skill_path: `ph-paper-helper`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

使用 paper-helper (ph) CLI 进行学术论文检索、导入与渐进式阅读。当 agent 需要搜索论文、调研研究方向、导入指定论文、获取完整 metadata、或精读全文时使用。覆盖完整工作流：快路径（search/add）→ 慢路径（fetch）→ SQL 查询本地库。适用场景包括"帮我找关于 X 的论文"、"调研 Y 方向的工作"、"精读这篇论文"、"搜索 Z 作者的研究"、"查一下本地收录了哪些论文"。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `ph-paper-helper/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
