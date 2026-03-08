---
name: tech-blog-writer
description: Generate Chinese technical blog posts that dissect the core philosophy behind a tool, library, framework, or technical approach. Use when the user asks to write a blog post, article, or introduction about a specific technology, or asks to explain/present a tool's design ideas in blog form. Triggers on requests like "write a blog post about X", "introduce X's philosophy", "explain why X does things differently".
---

# Tech Blog Writer

Generate a Chinese technical blog post that explains **why** a tool/approach exists and what design philosophy drives it, not just what it does.

## Workflow

### 1. Research

Before writing anything, build deep understanding:

- **Clone or read the source code.** Do not rely on README alone. Read the core modules, understand the data flow, find the design decisions embedded in code structure.
- **Read all available docs** (architecture, design, contributing guides, AGENTS.md, etc.).
- **Identify the "one big idea"** — every interesting project has a central tension it resolves differently from the mainstream. Find it.
- **Collect 4-6 code snippets** that embody the philosophy. Prefer short, self-contained functions that reveal design choices. Avoid showing boilerplate.

### 2. Find the contrast

The blog post must have an implicit or explicit **comparison anchor**:

- What is the mainstream way to solve this problem?
- What does this tool do differently, and what trade-off does that reflect?
- Do NOT write a generic "Tool A vs Tool B" comparison table. Instead, pick a specific design decision point and show how both sides handle it.

Example framings:
- "Most agents manage context with sliding windows. X uses an append-only tape."
- "Most frameworks give you a DSL. X says write plain Python."
- "Most CLIs guess what you mean. X requires a prefix character."

### 3. Write

Read [references/example-pi-post.md](references/example-pi-post.md) first as the gold-standard example. This is Armin Ronacher's post about Pi — study how it uses personal experience as entry point, weaves comparison implicitly, and lets code speak for design choices.

Then follow the structure and style rules in [references/style-guide.md](references/style-guide.md).

Key rules:
- **Chinese throughout.** Code comments can stay in English. Technical terms keep original English with Chinese context.
- **First person, conversational but technical.** Not academic, not casual.
- **Show code, then explain.** Code is evidence, prose is argument.
- **Every section must advance the "one big idea."** If a section doesn't connect back to the core philosophy, cut it.
- **Distinguish project claims from your analysis.** If the project says it, quote or attribute. If you inferred it, say so.

### 4. Self-check

Before presenting the final post:
- Does every code snippet come from the actual source? No fabricated examples.
- Is the "one big idea" clear within the first 3 paragraphs?
- Is there a concrete comparison with mainstream approaches?
- Would a reader who has never seen this tool understand both what it does AND why it does it that way?
- Are project statements vs personal analysis clearly distinguished?
