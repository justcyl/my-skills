# tm

- skill_id: `tm`
- status: `managed`
- skill_path: `tm`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

Remote GPU server management via `tm` CLI. Use when user needs to: (1) execute commands on remote servers, (2) run GPU training/evaluation experiments, (3) sync code to servers, (4) check GPU availability, (5) manage background jobs on servers. All operations are stateless SSH calls — develop locally, execute remotely.

## Risk Findings

- references sensitive ssh or aws paths

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `tm/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
