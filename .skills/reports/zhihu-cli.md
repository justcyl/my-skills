# zhihu-cli

- skill_id: `zhihu-cli`
- status: `managed`
- skill_path: `zhihu-cli`
- source_type: `github`
- source: `https://github.com/BAIGUANGMEI/zhihu-cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

知乎 CLI (pyzhihu-cli)：搜索、热榜、问题/回答/评论、推荐 Feed、用户资料、发想法/提问/文章、删自己的内容、点赞关注、收藏与通知。Agent 代执行 zhihu 命令，Cookie 仅存本地。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `zhihu-cli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
