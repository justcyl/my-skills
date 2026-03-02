# Skills Manager Design

Date: 2026-03-02

## Summary

Build a single control skill named `skills-manager` to manage all skills in this repository.

The repository `my-skills` becomes the single control plane for:

- importing external skills
- creating and bootstrapping new skills
- storing upstream and managed copies
- generating Chinese optimized managed versions
- scanning for prompt and script risks
- distributing managed skills to agent-specific skill directories
- committing and pushing changes back to GitHub

The design borrows two patterns from the referenced skills:

- `find-skills`: clear discovery and import flow
- `skill-creator`: concise entrypoint, progressive disclosure, modular references and scripts

## Goals

1. Replace ad hoc use of `npx skills`, `skills-refiner`, and manual copying with one management skill.
2. Use the current repository as the canonical home for all managed skills.
3. Keep a dual-track structure for every imported skill:
   - `upstream`: original imported version
   - `managed`: Chinese optimized version generated from upstream and later editable by hand
4. Support semi-automatic operation:
   - analysis and generation run automatically
   - distribution, overwrite, git commit, and git push require confirmation
5. Support at least Codex and Claude Code as distribution targets in the first version.

## Non-Goals

- Full compatibility with every `npx skills` provider and edge case in v1
- Deep malware detection or formal security guarantees
- Automatic merge resolution between upstream changes and hand-edited managed copies
- Scheduled background updates
- Building a separate standalone CLI first

## Design Principles

### Single Entry Skill

Expose one user-facing skill, `skills-manager`, instead of multiple sibling skills.

The single entrypoint improves trigger clarity and keeps the operator model simple:

- ask to find or import a skill
- ask to create or bootstrap a skill
- ask to update managed skills
- ask to distribute to agents
- ask to commit or push repository changes

### Progressive Disclosure

Keep `SKILL.md` short and procedural. Load detailed references only when needed.

This follows the structure style of `skill-creator`:

- main trigger metadata in frontmatter
- short routing logic in `SKILL.md`
- task-specific details in `references/`
- repetitive deterministic actions in `scripts/`

### Repository As Database

Treat the current repository as the durable state store for skill management.

All important state must live in versioned files inside the repo:

- source metadata
- upstream snapshots
- managed snapshots
- risk reports
- registry state
- agent distribution state

### Managed Copy Is The Only Distribution Source

Only distribute from `managed/`.

`upstream/` is archival and update reference material. It must not be edited manually in normal flow.

## High-Level Architecture

There are four layers:

1. `skills-manager/`
   The orchestrator skill that tells the model how to manage skills
2. `catalog/`
   Repository-resident state and managed skill content
3. `scripts/` inside `skills-manager/`
   Deterministic helpers for bootstrap, import, distribution, and publishing
4. agent skill directories
   Deployment targets populated by symlink first, copy as fallback

## Repository Layout

```text
my-skills/
├── skills-manager/
│   ├── SKILL.md
│   ├── agents/
│   │   └── openai.yaml
│   ├── references/
│   │   ├── overview.md
│   │   ├── find-and-import.md
│   │   ├── create-and-bootstrap.md
│   │   ├── update-and-refresh.md
│   │   ├── audit-and-risk.md
│   │   ├── refine-and-manage.md
│   │   ├── distribute-to-agents.md
│   │   ├── git-publish.md
│   │   └── catalog-schema.md
│   └── scripts/
│       ├── bootstrap_catalog.sh
│       ├── import_skill.sh
│       ├── sync_agents.sh
│       └── publish_repo.sh
├── catalog/
│   ├── skills/
│   │   └── <skill-id>/
│   │       ├── upstream/
│   │       └── managed/
│   ├── sources/
│   │   └── <skill-id>.json
│   ├── reports/
│   │   └── <skill-id>.md
│   ├── agents/
│   │   ├── codex.json
│   │   └── claude-code.json
│   └── locks/
│       └── registry.json
└── existing skill folders...
```

## Skill Structure

### Entry Skill

`skills-manager/SKILL.md` is the only trigger entrypoint.

Its job is to:

- recognize requests about discovering, importing, creating, updating, distributing, or publishing skills
- decide which reference modules to load
- enforce semi-automatic confirmation boundaries
- treat `my-skills` as the source of truth

### Reference Modules

The references are split by task:

- `overview.md`
  common rules, control plane assumptions, confirmation boundaries
- `find-and-import.md`
  discovery, source parsing, import flow
- `create-and-bootstrap.md`
  creating a new local skill and registering it in the catalog
- `update-and-refresh.md`
  upstream refresh and managed regeneration rules
- `audit-and-risk.md`
  static prompt and script risk screening heuristics
- `refine-and-manage.md`
  how to generate managed Chinese optimized copies from upstream
- `distribute-to-agents.md`
  symlink/copy rules and target directory mapping
- `git-publish.md`
  git status, commit, push, and failure handling
- `catalog-schema.md`
  canonical JSON and folder schema

### Scripts

The first version needs only a small number of helper scripts:

- `bootstrap_catalog.sh`
  register current repository skills as initial managed entries
- `import_skill.sh`
  import a local or remote source into a temp folder and stage catalog files
- `sync_agents.sh`
  distribute managed skills to supported agent directories
- `publish_repo.sh`
  validate git state and perform commit/push after confirmation

Scripts should use repository-relative paths internally and resolve absolute paths at runtime.

## Catalog Data Model

### Skill ID

Each skill gets a stable `skill_id`.

Rule:

- prefer current folder name
- normalize to kebab-case
- ensure uniqueness across the repository

The internal `skill_id` remains stable even if the human-facing `name:` in `SKILL.md` changes later.

### `catalog/sources/<skill-id>.json`

Purpose:

- record where the skill came from
- define update behavior
- mark whether upstream exists

Suggested fields:

```json
{
  "skill_id": "find-skills",
  "source_type": "github",
  "source": "vercel-labs/agent-skills",
  "source_url": "https://github.com/vercel-labs/agent-skills.git",
  "ref": "main",
  "subpath": "skills/find-skills",
  "bootstrap": false,
  "upstream_enabled": true,
  "last_imported_at": "2026-03-02T00:00:00Z",
  "upstream_revision": "abcdef123456",
  "managed_revision": "sha256:...",
  "managed_dirty": false
}
```

For existing local skills without known origin:

```json
{
  "source_type": "local-bootstrap",
  "bootstrap": true,
  "upstream_enabled": false
}
```

### `catalog/locks/registry.json`

Purpose:

- provide a single registry of all managed skills
- support quick status inspection and routing

Suggested per-skill state:

- `skill_id`
- `display_name`
- `status`
- `audit_status`
- `managed_dirty`
- `distribution`
- `has_upstream`
- `report_path`

### `catalog/reports/<skill-id>.md`

Each report should be short and operator-readable.

Suggested sections:

- source
- what the skill does
- how to use it
- risk summary
- managed generation summary
- last update summary

### `catalog/agents/<agent>.json`

Purpose:

- record what has been distributed
- track deploy mode
- support idempotent sync

Suggested fields:

- `skill_id`
- `source_path`
- `target_path`
- `mode`: `symlink` or `copy`
- `last_synced_at`
- `sync_status`

## Core Workflows

### 1. Import External Skill

Trigger examples:

- "import this repo as a skill"
- "download this skill into my repository"
- "find a skill for X and add it here"

Flow:

1. parse source from repo shorthand, URL, local path, or well-known endpoint
2. fetch source into a temp directory
3. discover valid `SKILL.md` candidates
4. run static risk screening
5. save original files to `catalog/skills/<skill-id>/upstream/`
6. ask the model to generate Chinese optimized `managed/` from upstream
7. write source metadata and report
8. update registry
9. ask whether to distribute
10. ask whether to commit and push

Automatic:

- fetch
- discovery
- screening
- upstream save
- managed generation
- report generation

Confirmation required:

- overwrite existing skill id
- distribute to agents
- git commit and push

### 2. Create New Local Skill

Trigger examples:

- "create a new skill for X"
- "bootstrap a skill from this folder"
- "turn this workflow into a skill"

Flow:

1. route to `create-and-bootstrap.md`
2. create a new skill folder using the repository's conventions
3. write `SKILL.md`
4. optionally create `references/`, `scripts/`, `agents/openai.yaml`
5. register the skill directly as `managed/`
6. mark source as `local-bootstrap`
7. generate a report and registry entry
8. optionally distribute and publish

This absorbs the useful parts of `skill-creator` without exposing a second public skill.

### 3. Update Existing Skill

Trigger examples:

- "update this managed skill"
- "refresh all upstream skills"
- "pull latest changes for X"

Flow:

1. read `catalog/sources/<skill-id>.json`
2. if `upstream_enabled` is false, report that only local managed editing is available
3. fetch latest upstream source
4. compare `upstream_revision`
5. if changed:
   - replace `upstream/`
   - re-run risk screening
   - regenerate `managed/` from new upstream
6. if `managed_dirty` is true, stop before overwrite and ask for confirmation
7. rewrite report
8. update registry
9. ask whether to redistribute
10. ask whether to commit and push

### 4. Manual Managed Editing

Policy:

- manual edits happen only in `managed/`
- never hand-edit `upstream/`

After a manual edit:

1. recompute managed hash
2. set `managed_dirty = true`
3. update registry and report if needed
4. optionally redistribute
5. optionally commit and push

### 5. Distribute To Agents

First version supports:

- Codex
- Claude Code

Source of truth:

- always distribute from `catalog/skills/<skill-id>/managed/`

Deploy order:

1. resolve target directories
2. attempt symlink
3. if symlink fails, fallback to copy
4. update `catalog/agents/<agent>.json`
5. summarize results for the user

Confirmation required before any distribution.

## Risk Screening

This is a heuristic static screen, not a full security guarantee.

Checks should include:

- shell commands that mutate sensitive locations
- references to `~/.ssh`, `~/.aws`, tokens, secrets, keyrings
- instructions to ignore policy or bypass system constraints
- downloading and executing remote content without verification
- ambiguous prompts requesting broad unrestricted access

Output levels:

- `passed`
- `warned`
- `blocked`

Policy:

- `warned`: import allowed, distribution requires explicit confirmation
- `blocked`: upstream may be stored for inspection, automatic managed generation and distribution should pause pending confirmation

## Managed Generation Strategy

Keep this simple in v1.

For every imported upstream skill:

1. preserve upstream as-is
2. ask the model to generate a Chinese optimized managed copy
3. keep structure and scripts unless there is a clear reason to change them
4. improve clarity, trigger wording, modular references, and workflow quality
5. write a short generation summary into the report

No separate refine modes are needed in v1.

## Git Integration

Repository publishing is part of the management workflow.

After import, update, or manual managed edits:

1. inspect git status
2. summarize changed files
3. propose a concise commit message
4. commit after confirmation
5. push to current `origin` after confirmation

If push fails:

- keep the local commit
- report the error
- do not roll back

## Initial Bootstrap Plan

Current repository skills become the initial managed dataset.

Bootstrap steps:

1. scan existing skill folders in repository root
2. create `catalog/skills/<skill-id>/managed/` for each
3. copy current skill contents into managed
4. generate `catalog/sources/<skill-id>.json` with `source_type = local-bootstrap`
5. generate short reports
6. populate `catalog/locks/registry.json`

In bootstrap phase:

- do not invent upstream sources
- do not create fake upstream revisions
- do not force immediate distribution changes

Later, explicit source registration can enable upstream refresh for a bootstrapped skill.

## Semi-Automatic Confirmation Boundaries

The skill should ask before:

- overwriting an existing managed skill
- overwriting a manually edited managed copy during update
- distributing to any agent directories
- committing changes
- pushing changes

The skill may proceed automatically for:

- discovery
- temp download
- risk scan
- upstream persistence
- managed generation
- registry update
- report generation

## MVP Scope

Version 1 includes:

- one `skills-manager` skill
- modular references and minimal scripts
- bootstrap current repository skills into catalog
- import from GitHub URL, shorthand, and local path
- heuristic static risk screen
- generate Chinese optimized managed copy from upstream
- distribute to Codex and Claude Code
- commit and push after confirmation

Version 1 excludes:

- scheduled updates
- rich merge tooling
- full provider registry parity with `npx skills`
- deep vulnerability intelligence feeds
- broad multi-agent support beyond the first two targets

## Recommended Implementation Order

1. create design document
2. create `skills-manager/` skeleton
3. define `catalog` schema
4. implement bootstrap for current repository skills
5. implement import flow
6. implement risk screening and managed generation
7. implement agent distribution
8. implement git publish helpers

## Open Question

The design assumes the final public entry skill name is `skills-manager`.

If a shorter or more repository-branded name is preferred later, rename before implementation starts so `skill_id`, metadata, and user-facing trigger language stay consistent.
