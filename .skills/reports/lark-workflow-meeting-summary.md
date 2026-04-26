# lark-workflow-meeting-summary

- skill_id: `lark-workflow-meeting-summary`
- status: `imported`
- skill_path: `lark-workflow-meeting-summary`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

会议纪要整理工作流：汇总指定时间范围内的会议纪要并生成结构化报告。当用户需要整理会议纪要、生成会议周报、回顾一段时间内的会议内容时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-workflow-meeting-summary/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
