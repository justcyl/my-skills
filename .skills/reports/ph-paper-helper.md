# ph-paper-helper

- skill_id: `ph-paper-helper`
- status: `managed`
- skill_path: `ph-paper-helper`
- source_type: `local-created`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

学术论文检索与管理的首选方案。当需要搜索论文、调研某个研究方向、导入指定论文、导出 BibTeX、或精读全文时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `ph-paper-helper/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
