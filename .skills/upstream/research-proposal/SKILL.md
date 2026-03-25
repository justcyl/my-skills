---
name: research-proposal
description: >
  Write a structured ML/AI research proposal from a user's idea. Use this skill whenever the user
  wants to turn a research idea, hypothesis, or method sketch into a full proposal document —
  including when they mention "proposal", "research plan", "experiment plan", "paper idea",
  "write up my idea", or describe a hypothesis they want to test. Also trigger when the user
  provides a rough idea and asks for structure, a related-work section, an experiment design,
  or success criteria.
---

# Research Proposal Skill

This skill turns a user's research idea into a structured, executable proposal in Markdown.
The proposal format is designed for short empirical papers at top ML/AI conferences, with
emphasis on clear hypotheses, pre-registered success criteria, and reproducible experiment plans. The output is a comprehensive Markdown proposal suitable for guiding verification experiments at top AI venues (NeurIPS, ICML, ICLR, ACL, EMNLP, etc.).

## Before you start

Read the template and writing guide in `references/template_guide.md` (in the same directory
as this SKILL.md). That file contains the full section-by-section template with field
descriptions, examples, and common pitfalls. Always consult it before drafting.

## Workflow

### Step 1: Understand the idea

Gather from the user (ask if missing):

1. **What is the core hypothesis or claim?** (e.g., "Method X will match Method Y at lower cost")
2. **What is the proposed method / intervention?** (even a rough sketch is fine)
3. **What baseline(s) does it compare against?**
4. **What task / benchmark / dataset will be used?**
5. **What is the paper type?** Default: short empirical paper.
6. **Any compute or resource constraints?**

You do not need all answers upfront — make reasonable defaults and flag assumptions.

### Step 2: Research (if tools available)

If web search is available, search for:
- The closest prior work to check novelty
- The specific benchmarks / datasets mentioned
- Recent related papers in the same area (last 1–2 years)

If no search is available, work from the user's description and your training knowledge,
and flag areas where the user should verify novelty.

### Step 3: Draft the proposal

Follow the template in `references/template_guide.md` exactly. Key principles:

- **Be concrete, not vague.** Every section should contain specifics: model names with
  HuggingFace links, dataset sizes, hyperparameter values, GPU-hour estimates.
- **Pre-register success criteria.** Define numeric thresholds for "proceed", "refute",
  and "pivot" before results are known. Fill result cells with **TBD**.
- **Acknowledge failure modes.** Each hypothesis section should explain how the idea could
  be wrong. The Impact Statement should discuss both success and failure outcomes.
- **Use tables liberally.** Taxonomy tables, comparison tables, results tables, and
  ablation tables make the proposal scannable.
- **Keep related work honest.** Include a "Novelty Kill Search Summary" stating what
  you searched for and what you found (or didn't find).

### Step 4: Output

Produce the proposal as a single Markdown file. Use the `create_file` tool to write it
to `/mnt/user-data/outputs/` with a descriptive filename (e.g., the proposal title in
snake_case with `.md` extension). Then present the file to the user.

## Quality checklist (self-review before presenting)

Before presenting the final proposal, verify:

- [ ] Every section from the template is present (even if brief)
- [ ] Hypothesis is falsifiable with a concrete decision rule
- [ ] At least one baseline is specified with source/link
- [ ] Results table has TBD cells (not fabricated numbers)
- [ ] Ablation table exists with ≥1 variant
- [ ] Resource estimate is included with GPU-hour budget
- [ ] Impact Statement covers both success and failure cases
- [ ] References section lists all cited works
- [ ] Math uses `\(...\)` for inline and `\[...\]` for display formulas
