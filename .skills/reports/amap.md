# amap

- skill_id: `amap`
- status: `managed`
- skill_path: `amap`
- source_type: `github`
- source: `https://github.com/kaichen/amap-skill`
- upstream_enabled: `true`
- risk_status: `warned`

## Summary

通过脚本直连高德 Web Service API 完成地理编码、逆地理编码、IP 定位、天气、路径规划、距离测量和 POI 查询。用户要求“高德/AMap 查询”“路线规划”“地理编码”“POI 搜索”或需要用命令行脚本调用高德 API 时使用。

## Risk Findings

- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `amap/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
