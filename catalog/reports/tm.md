# tm

- skill_id: `tm`
- status: bootstrapped
- source_type: `local-bootstrap`
- upstream_enabled: `false`
- managed_path: `catalog/skills/tm/managed`

## Summary

Remote GPU server management via `tm` CLI. Use when user needs to: (1) execute commands on remote servers, (2) run GPU training/evaluation experiments, (3) sync code to servers, (4) check GPU availability, (5) manage background jobs on servers. All operations are stateless SSH calls — develop locally, execute remotely.

## Notes

- This skill was registered from the current repository as part of the initial bootstrap.
- No upstream source is configured yet.
- Future updates require either manual edits in `managed/` or explicit source registration.
