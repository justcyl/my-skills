# lark-apps

- skill_id: `lark-apps`
- status: `managed`
- skill_path: `lark-apps`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

妙搭（Spark/Miaoda）应用开发与托管：应用创建、HTML静态站点发布、本地全栈开发、云端生成迭代。当用户要开发/新建一个系统·工具·平台·应用，或要本地开发 / 云端开发 / 修改 / 部署 / 发布 / 上线 / 拿可分享链接，或用 HTML 做页面·网站给人看，或提到妙搭/Spark/Miaoda、应用数据库、可见范围时使用。不负责普通云盘文件上传（lark-drive）、飞书文档编辑（lark-doc）、原生幻灯片创建（lark-slides）。

## Risk Findings

- references sensitive ssh or aws paths
- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-apps/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
