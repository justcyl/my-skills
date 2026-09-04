# add-svg

- skill_id: `add-svg`
- status: `managed`
- skill_path: `add-svg`
- source_type: `local`
- source: `/Users/chenyl/Documents/Codex/2026-07-28/https-github-com-qianjinydx-research-drawio/work/research-drawio-skill-source`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

Add, collect, design, audit, and integrate SVG elements into editable
diagrams.net/draw.io scientific figures. Use when the user asks to supplement
a draw.io diagram with SVG icons, mechanisms, biological objects, model
components, pathway symbols, instruments, graphical abstract elements, or
publication-style vector assets. Every execution must first ask the user to
choose the SVG source mode: network search or self-designed SVG. For network
mode, search for multiple relevant SVG candidates for later user selection,
record sources and license notes, and fall back to self-designed SVG for
concepts with no suitable result. For self-design mode, create restrained,
editable, Nature-style SVGs from simple vector primitives. Use with .drawio,
SVG, diagrams.net, 科研流程图, 论文示意图, SVG补图, 图标补充, and draw.io配图.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `add-svg/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
