# anyone-to-skill

- skill_id: `anyone-to-skill`
- status: `managed`
- skill_path: `anyone-to-skill`
- source_type: `github`
- source: `https://github.com/OpenDemon/anyone-to-skill.git`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

两种模式：
① 明确角色扮演：仅当用户明确要求“扮演 / 模拟 / 用某人语气回答”时，切换到对应人物风格。
如果用户只是问“某人会怎么看”，默认先用普通分析口吻总结其可能观点，不直接进入第一人称扮演。
② 蒸馏新人物：当用户明确要求“把这些材料做成 skill / 蒸馏某人”时，先确认材料授权、输出目录、是否允许联网与执行命令，再运行蒸馏流水线。
触发信号：明确角色扮演；明确蒸馏/生成 skill；避免对普通比较分析误触发。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `anyone-to-skill/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
