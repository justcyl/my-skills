# lark-minutes

- skill_id: `lark-minutes`
- status: `imported`
- skill_path: `lark-minutes`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书妙记：妙记相关基本功能。1.查询妙记列表（按关键词/所有者/参与者/时间范围）；2.获取妙记基础信息（标题、封面、时长 等）；3.下载妙记音视频文件；4.获取妙记相关 AI 产物（总结、待办、章节）。飞书妙记 URL 格式: http(s)://<host>/minutes/<minute-token>

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-minutes/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
