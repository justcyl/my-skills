# Research Proposal Template & Writing Guide

This document defines the exact structure, section-by-section guidance, and writing
conventions for producing a structured ML/AI research proposal.

---

## Table of Contents

1. [Full Template Skeleton](#1-full-template-skeleton)
2. [Section-by-Section Guide](#2-section-by-section-guide)
3. [Tables Reference](#3-tables-reference)
4. [Writing Conventions](#4-writing-conventions)
5. [Common Pitfalls](#5-common-pitfalls)

---

## 1. Full Template Skeleton

Below is the complete section hierarchy. Every proposal MUST include all of these
sections. If a section is not applicable, include it with a brief explanation of why
(e.g., "No training data needed — inference-only evaluation.").

```
# [Full Proposal Title]

## Scope and Constraints
## Introduction
  ### Context and Motivation
  ### The Problem
  ### Key Insight and Hypothesis
## Proposed Approach
  ### Overview
  ### Method Details
  ### Key Innovations
## Related Work
  ### Field Overview
  ### Related Papers
  ### Taxonomy
  ### Closest Prior Work
  ### Comparison Table
## Experiments
  ### Experimental Setup
  ### Benchmarks and Metrics
  ### Main Results
  ### Ablation Studies
  ### Experimental Rigor
## Success Criteria
## Impact Statement
## References
```

---

## 2. Section-by-Section Guide

### Title

A descriptive, specific title that conveys both the method and the evaluation target.
Pattern: "[Method Noun] for [Problem] via [Mechanism]" or
"[Evaluation Type] of [System] on [Task]".

Good: "Debiased One-Pass Attention Sorting for Long-Context QA via Per-Prompt
Position-Bias Estimation"
Bad: "Improving Long-Context Models" (too vague)

---

### Scope and Constraints

A short metadata block. Include:

- **Paper Type**: Short paper / Full paper
- **Target Venues**: List 2–5 specific venues (e.g., NeurIPS, ICML, ICLR, ACL, EMNLP)
- **Core constraint** (optional): e.g., "Fully automated evaluation", "No human eval"
- **Verification budget** (optional): e.g., "≤ 768 A100-hours total"

---

### Introduction

Three mandatory subsections:

#### Context and Motivation

- Set the scene: what area is this in, and why does it matter now?
- Introduce the key prior work that this proposal builds on (with references).
- Explain the practical motivation — who cares and why?
- Length: 2–4 paragraphs.

#### The Problem

- State the specific gap, limitation, or unanswered question.
- Be precise about what is wrong or missing — use numbers if available
  (e.g., "requires 2–5 re-sorting iterations, each with a full prefill pass").
- If the problem comes from a specific paper's limitation, cite it directly.
- Length: 1–3 paragraphs.

#### Key Insight and Hypothesis

- State the hypothesis as a bold, testable claim. Use **Hypothesis.** as a lead-in.
- Explain the mechanistic reasoning: why should this work?
- Explicitly list reasons it could fail (2–3 bullet points or a short paragraph
  starting with "This can fail if..." or "Why we could be wrong:").
- Length: 2–3 paragraphs.

---

### Proposed Approach

Three mandatory subsections:

#### Overview

- A high-level summary of the method in 1 paragraph or a numbered list of steps.
- State the key computational property (e.g., "uses the same number of forward
  passes as k=1 Attention Sorting").

#### Method Details

- The technical core. Include:
  - Setup and notation (define variables, dimensions, inputs/outputs)
  - Mathematical formulations with display equations where appropriate
  - Algorithmic steps or pseudocode
  - Implementation notes (e.g., library choices, precision, fallback strategies)
- Use subsubheadings (####) to break up long method sections.
- Be specific enough that someone could implement this from the proposal alone.

#### Key Innovations

- A numbered list of 2–4 bullet points, each stating one novel contribution.
- Each bullet should distinguish what is new from what is borrowed from prior work.

---

### Related Work

Five mandatory subsections:

#### Field Overview

- A 1–2 paragraph narrative placing this work in the broader landscape.
- Identify 3–5 research families/clusters that are relevant.

#### Related Papers

- A bullet list of 15–30 related papers, each with:
  - **[Paper Title](link)**: One-sentence description of what it does and why
    it is relevant.
- Include the most important papers (direct baselines, closest competitors) first.
- Include both classic and recent (last 1–2 years) work.

#### Taxonomy

A table organizing related work into families:

| Family / cluster | Core idea | Representative papers | Benchmarks / evaluation | Known limitations |
|---|---|---|---|---|

- Aim for 4–7 rows covering the main research clusters.

#### Closest Prior Work

- For each of the 3–5 most closely related papers, write a paragraph explaining:
  - What it does
  - How it differs from this proposal
  - Why this proposal's approach should improve on it
- Include a **Novelty Kill Search Summary**: state what search queries you ran
  (or the user should run) and whether any prior work was found that already
  proposes the same idea. Example:
  "Searched for 'X + Y + Z' combinations. No prior work proposing [specific
  combination] was found as of [date]."

#### Comparison Table

A table directly comparing this proposal against 4–6 closest works:

| Related work | What it does | Key limitation | What we change | Why ours should win |
|---|---|---|---|---|

---

### Experiments

Five mandatory subsections:

#### Experimental Setup

Include ALL of the following (use "N/A" if not applicable):

- **Primary benchmark**: Name, source, size, why it was chosen.
- **Base model(s)**: Exact model name with HuggingFace/download link.
  If multiple models, list them in a table.
- **Baseline Ladder**: A numbered list of baselines from weakest to strongest:
  - Level 1 (prompting): simplest baseline
  - Level 2–4 (increasingly strong): task-specific or method-specific baselines
  - Level 5 (closest method): the strongest known comparable method
- **Main conditions**: List all experimental conditions (e.g., A, B, C + ablation).
  Give each a short label and a one-line description.
- **Implementation notes**: attention to practical details (precision, library
  versions, fallback strategies).
- **Training Data** (if applicable): Table with dataset name, purpose, size,
  download link, and license.
- **Resource Estimate**: Include compute budget in GPU-hours with rationale,
  GPU memory requirements, and whether external APIs are needed.

#### Benchmarks and Metrics

A table:

| Benchmark | Description | Metrics | Split | Download Link | Evaluation Script |
|---|---|---|---|---|---|

#### Main Results

A results table with all cells marked **TBD**:

| Method | Base Model | Benchmark | [Primary Metric] (mean±std) | [Secondary Metric] | Source | Notes |
|---|---|---|---|---|---|---|

- Include rows for every condition in the Experimental Setup.
- Add a "Source" column for citing published numbers (use "–" for new experiments).

#### Ablation Studies

A table:

| Variant | What's changed | Expected finding |
|---|---|---|

- Include at least 1 ablation. Typically 2–4 is ideal.
- Each ablation should isolate one design choice.

#### Experimental Rigor

Address:

- **Variance & Reproducibility**: How many seeds? What is held fixed?
  (e.g., "3 random seeds for shuffling; greedy decoding for determinism")
- **Validity & Controls**: Pre-registered sanity checks, phase gates, confound
  controls. Example: "Phase-0 gate: on 50 prompts, check if metric improves
  before running full evaluation."
- **Sanity checks**: What trivial conditions should hold?
  (e.g., "Random baseline should score ~0")

---

### Success Criteria

This section is critical. It pre-registers the decision rules BEFORE experiments run.

Required structure:

1. **Hypothesis** (restate in one sentence).
2. **Decision Rule** with three labeled outcomes:
   - **Proceed** (hypothesis supported): Specific numeric threshold
     (e.g., "within 2 points of baseline X").
   - **Refute** (hypothesis rejected): Specific numeric threshold
     (e.g., "≥3 points worse than baseline X").
   - **Pivot** (intermediate result): What to try next if results are ambiguous.
3. (Optional) **Precondition / regime check**: A sanity test that must pass before
   the main hypothesis is evaluated (e.g., "the baseline must show a non-trivial
   gain over no intervention").

Use concrete numbers, not vague language like "significantly better".

---

### Impact Statement

Two paragraphs:

1. **If successful**: What changes for the field/practitioners? Be specific.
2. **If it fails**: Why is the negative result still informative? What does it
   tell us about the problem or the design space?

This dual-outcome framing is essential — every proposal should be worth running
regardless of outcome.

---

### References

A bullet list of all cited works in this format:

```
- [Paper Title](URL) — Authors, Year
```

Or if referencing a local file:

```
- [Paper Title](./references/path/to/meta_info.txt) - Authors, Year
```

---

## 3. Tables Reference

The proposal uses several standard table formats. Here is a quick reference:

### Taxonomy Table
| Family / cluster | Core idea | Representative papers | Benchmarks / evaluation | Known limitations |
|---|---|---|---|---|

### Comparison Table
| Related work | What it does | Key limitation | What we change | Why ours should win |
|---|---|---|---|---|

### Benchmarks Table
| Benchmark | Description | Metrics | Split | Download Link | Evaluation Script |
|---|---|---|---|---|---|

### Results Table
| Method | Base Model | Benchmark | [Metric] (mean±std) | Source | Notes |
|---|---|---|---|---|---|

### Ablation Table
| Variant | What's changed | Expected finding |
|---|---|---|

### Base Models Table (optional, for multi-model setups)
| Model | Size | Download Link | Notes |
|---|---|---|---|

### Training Data Table (optional)
| Dataset | Purpose | Size | Download Link | License |
|---|---|---|---|---|

---

## 4. Writing Conventions

### Math formatting
- Inline math: `\(...\)` (NOT `$...$`)
- Display math: `\[...\]` (NOT `$$...$$`)
- Keep notation consistent throughout: define once in Method Details, reuse everywhere.

### Tone and style
- Write in first-person plural ("We propose...", "Our method...").
- Be direct and specific — avoid hedging language like "may potentially help".
- Use bold for key terms on first introduction.
- Use horizontal rules (`---`) to separate major sections visually.

### Links and citations
- Link to arXiv, HuggingFace, or GitHub whenever possible.
- For papers referenced in the proposal's own repo structure, use relative paths.
- For external papers, prefer arXiv URLs.

### TBD Convention
- All result cells that depend on experiments MUST be **TBD**.
- Never fabricate or estimate numbers for the results table.
- Expected findings in ablation tables can describe qualitative expectations.

---

## 5. Common Pitfalls

1. **Vague hypothesis**: "Our method will improve performance" →
   Fix: "Debiased k=1 sorting will match k=5 accuracy within 2 points on SynthWiki."

2. **Missing failure analysis**: Not explaining how the idea could be wrong →
   Fix: Always include "This can fail if..." or "Why we could be wrong:".

3. **No compute budget**: Reviewers need to judge feasibility →
   Fix: Always include GPU-hours estimate with rationale.

4. **Fabricated baselines**: Guessing at baseline numbers →
   Fix: Mark everything as TBD; cite published numbers only with source.

5. **Forgetting the Novelty Kill Search**: Not checking if someone already did this →
   Fix: Always include search terms and date of search.

6. **One-sided Impact Statement**: Only discussing the success case →
   Fix: Always discuss both outcomes (success + failure).

7. **No ablation**: Hard to know which component matters →
   Fix: Always include ≥1 ablation isolating a key design choice.

8. **Missing seeds / variance**: Single-run results are unreliable →
   Fix: Pre-register number of seeds and report mean±std.
