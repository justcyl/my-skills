# lark-im

- skill_id: `lark-im`
- status: `managed`
- skill_path: `lark-im`
- source_type: `github`
- source: `https://github.com/larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

飞书即时通讯：收发消息和管理群聊。发送和回复消息、搜索聊天记录、管理群聊成员、上传下载图片和文件（支持大文件分片下载）、管理表情回复。当用户需要发消息、查看或搜索聊天记录、下载聊天中的文件、查看群成员时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-im/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
