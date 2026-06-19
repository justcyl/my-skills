# lark-calendar

- skill_id: `lark-calendar`
- status: `managed`
- skill_path: `lark-calendar`
- source_type: `github`
- source: `larksuite/cli`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

飞书日历：管理日历日程和会议室。查看/搜索日程、创建/更新日程、管理参会人、查询忙闲和推荐时段、预定会议室。当用户需要查看日程安排、创建/修改会议、查询/预定会议室时使用。不负责：查询过去的视频会议记录（走 lark-vc）、待办任务（走 lark-task）。

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `lark-calendar/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
