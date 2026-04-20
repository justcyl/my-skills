---
name: visual-checker
description: Visual QA sub-agent for AI-generated images. Spawns a dedicated pi sub-agent via herdr to evaluate image quality, content fidelity, and scene-specific criteria (academic / slides / general). Returns structured pass/fail report with regeneration guidance. Use when you need programmatic visual QA on a generated figure, diagram, or slide.
---

# Figure Checker

Visual QA sub-agent for AI-generated images. It compresses the image, reads it with vision, evaluates against scene-specific checklists, and outputs a structured `## Figure QA Report` with pass/fail verdict and regeneration guidance.

## When To Use

- You just generated a figure and need to verify quality before returning it
- You are running a generation pipeline (e.g., academic-paper, rhetoric-of-decks) and need automatic visual QA
- You want structured, actionable feedback for regeneration

## Input

Prepare three values before invoking:

| Field | Required | Values |
|-------|----------|--------|
| `image_path` | ✅ | Absolute path to `.png`, `.jpg`, `.jpeg`, `.webp`, or `.gif` |
| `scene` | ✅ | `academic` / `slides` / `general` |
| `intent` | ✅ | One sentence describing what the image should show |
| `extra` | ❌ | Additional context (e.g., "this is figure 2 in the paper") |

**Scene guidance:**
- `academic` — checks flat vector style, clean background, readable labels, publication-quality aesthetics
- `slides` — checks text size for projection, contrast, layout balance, no overflow
- `general` — checks content fidelity, visual quality, artifacts, text rendering, proportions

## Invocation via herdr

The visual-checker runs as a **separate pi sub-agent** in a herdr pane. Use four steps:

### Step 1 — Split a new pane

```json
{
  "action": "pane_split",
  "direction": "down",
  "newPane": "figure-qa"
}
```

### Step 2 — Run the sub-agent

Use the `invoke.sh` helper to avoid shell escaping issues with multiline content:

```json
{
  "action": "run",
  "pane": "figure-qa",
  "command": "bash ~/.agents/skills/visual-checker/scripts/invoke.sh '<image_path>' '<scene>' '<intent>'"
}
```

With optional extra context:

```json
{
  "action": "run",
  "pane": "figure-qa",
  "command": "bash ~/.agents/skills/visual-checker/scripts/invoke.sh '/tmp/fig.png' 'academic' 'Pipeline overview of our method' 'This is Figure 1 in the paper'"
}
```

> **What `invoke.sh` does internally:**  
> Loads the system prompt from `scripts/prompt.md`, then calls:  
> `pi --print --model axonhub/gemini-3.1-pro-preview --thinking off --tools read,bash --no-skills --no-context-files --no-extensions --no-session --system-prompt "..." "<user input>"`

### Step 3 — Wait for the sub-agent to finish

```json
{
  "action": "wait_agent",
  "pane": "figure-qa",
  "statuses": ["done", "idle"],
  "timeout": 120000
}
```

If it times out, read whatever output is available and surface the partial result.

### Step 4 — Read the QA report

```json
{
  "action": "read",
  "pane": "figure-qa",
  "source": "recent-unwrapped",
  "lines": 100
}
```

Locate the `## Figure QA Report` section in the output.

## Output Format

```markdown
## Figure QA Report

**File**: <image_path>
**Scene**: <academic | slides | general>
**Verdict**: ✅ PASS / ⚠️ MINOR ISSUES / ❌ REGENERATE

### Summary
<One sentence on overall quality>

### Issues Found

| Severity | Issue | Location |
|----------|-------|----------|
| Critical | <e.g. garbled text in title> | top-left |
| Minor    | <e.g. slightly off color>    | background |

### What's Good
- <genuine positives>

### Regeneration Guidance
<If REGENERATE: specific prompt edits to fix the issues.
 If PASS or MINOR: "No regeneration needed" or "Optional: ...">
```

## Handling Results

| Verdict | Action |
|---------|--------|
| ✅ PASS | Proceed with the image as-is |
| ⚠️ MINOR ISSUES | Optionally regenerate; minor issues may be acceptable |
| ❌ REGENERATE | Feed "Regeneration Guidance" back into the generation call and retry |

## Batch QA

For checking multiple images (e.g., all slides in a deck), reuse the same pane:

```
run → wait_agent → read → run → wait_agent → read → ...
```

No need to split a new pane between checks.

## Pane Cleanup

After all checks are done, stop the pane:

```json
{
  "action": "stop",
  "pane": "figure-qa"
}
```

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `invoke.sh: No such file` | Skill not distributed to `~/.agents/skills/` | Run `distribute_skills.sh` |
| `Image not found` | Wrong absolute path | Verify the path exists before calling |
| `Model not found` | `axonhub/gemini-3.1-pro-preview` not configured | Check `~/.pi/agent/models.json` |
| Pane never becomes `done` | Sub-agent hung or model error | Check with `herdr read --pane figure-qa --source recent-unwrapped` |

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — invocation guide |
| `scripts/invoke.sh` | Helper: builds the pi command and runs it |
| `scripts/prompt.md` | Figure-checker system prompt (loaded by invoke.sh) |
