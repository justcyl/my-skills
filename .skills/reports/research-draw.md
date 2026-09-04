# research-draw

- skill_id: `research-draw`
- status: `managed`
- skill_path: `research-draw`
- source_type: `local`
- source: `/Users/chenyl/Documents/Codex/2026-07-28/https-github-com-qianjinydx-research-drawio/work/research-drawio-skill-source`
- upstream_enabled: `true`
- risk_status: `passed`

## Summary

Two-stage workflow for publication-style scientific schematics: generate or
use a raster reference with imagegen/PNG/JPG/WebP, then trace it into an
editable diagrams.net/draw.io file using research-drawio-skill. Use for
Nature-style scientific illustrations, graphical abstracts, model or mechanism
schematics, biomedical workflows, AI architecture figures, and paper-style
visual drafts that should become editable .drawio source. For complex
recognizable elements, author or select dedicated SVG glyphs and compare
rendered SVGs against reference crops before inserting them, instead of
assembling those elements from draw.io primitives. Enforces a minimum
three-round strict pixel-level export/compare/fix loop for close
raster-to-draw.io tracing tasks. Use with imagegen, draw.io, diagrams.net,
scientific illustration, graphical abstract, paper schematic, figure tracing,
SVG glyph tracing, and drawio redraw requests.

## Risk Findings

- No heuristic findings.

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `research-draw/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
