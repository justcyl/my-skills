# Catalog Schema

## Directory Layout

```text
catalog/
├── skills/<skill-id>/
│   ├── upstream/
│   └── managed/
├── sources/<skill-id>.json
├── reports/<skill-id>.md
├── agents/<agent>.json
└── locks/registry.json
```

## `sources/<skill-id>.json`

Recommended fields:

```json
{
  "skill_id": "example-skill",
  "source_type": "local-bootstrap",
  "source": "",
  "source_url": "",
  "ref": "",
  "subpath": "",
  "bootstrap": true,
  "upstream_enabled": false,
  "last_imported_at": "",
  "upstream_revision": "",
  "managed_revision": "",
  "managed_dirty": false
}
```

## `locks/registry.json`

Recommended fields:

```json
{
  "version": 1,
  "skills": {}
}
```

## `agents/<agent>.json`

Recommended fields:

```json
{
  "version": 1,
  "agent": "codex",
  "skills": {}
}
```
