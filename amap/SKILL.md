---
name: amap
description: 通过脚本直连高德 Web Service API 完成地理编码、逆地理编码、IP 定位、天气、路径规划、距离测量和 POI 查询。用户要求“高德/AMap 查询”“路线规划”“地理编码”“POI 搜索”或需要用命令行脚本调用高德 API 时使用。
---

# AMap Skill

通过本地 Bun 脚本调用高德 Web Service API，适合把自然语言里的地址、坐标、路线、天气、POI 查询转换为稳定的命令行调用。

## Quick Start
1. Ensure `AMAP_MAPS_API_KEY` is set.
2. Run `bun scripts/amap.ts --help` in this skill directory.
3. Pick the matching command from `references/command-map.md`.

## Workflow
1. Validate user intent and select one command.
2. Prefer address commands for route planning when users provide plain addresses.
3. Keep output as raw AMap JSON without wrapping fields.
4. Treat any non-zero API business state as failure.
5. Run commands from this skill directory unless using absolute script paths.

## Commands
- Full command mapping: `references/command-map.md`
- Ready-to-run examples: `references/examples.md`

## Safety
- Read the API key only from `AMAP_MAPS_API_KEY`; do not ask the user to paste real keys into chat.
- Do not write API keys into tracked files, examples, shell history snippets, or reports.
- The heuristic audit warning is expected because this skill documents the required API-key environment variable.

## 中文说明
- 触发条件：用户要求高德/AMap 查询、地理编码、逆地理编码、天气、路线规划、距离测量、POI 搜索。
- 对地址输入优先使用 `*-route-address` 命令；用户已经给经纬度时使用 `*-route-coords`。
- 输出保持高德原始 JSON，除非用户明确要求摘要或解释。
- 运行前确认本机已安装 `bun`，并且环境变量 `AMAP_MAPS_API_KEY` 可用。

## Notes
- This skill is script-first and does not run an MCP server.
- Only `AMAP_MAPS_API_KEY` is supported.
