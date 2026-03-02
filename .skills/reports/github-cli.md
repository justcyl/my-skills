# github-cli

- skill_id: `github-cli`
- status: `managed`
- skill_path: `github-cli`
- source_type: `local-bootstrap`
- source: ``
- upstream_enabled: `false`
- risk_status: `warned`

## Summary

GitHub CLI (gh) reference for repositories, issues, pull requests, Actions, projects, releases, gists, codespaces, and GitHub operations from the command line.

## Risk Findings

- references sensitive ssh or aws paths
- mentions secrets, tokens, or private keys

## Boundaries

- Script-generated state lives in `.skills/`.
- Skill content lives directly in `github-cli/`.
- LLM review should focus on semantics, prompt safety, and Chinese optimization.
