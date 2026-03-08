# Style Guide

## Voice

- First person singular. "I" looked at this, "I" tried that.
- Conversational but never sloppy. Treat the reader as a working engineer.
- Have opinions. "I think this matters" is better than "this might be worth considering."
- Acknowledge trade-offs honestly. Never claim something is strictly better without saying what it costs.

## Structure Template

A post follows this arc:

```
1. Hook (1-2 paragraphs)
   Personal entry point. Why you looked at this, what caught your attention.
   Do NOT open with "there are many X tools" — find a specific angle.

2. What it is (2-3 paragraphs)
   Minimal context. Enough for someone who hasn't seen it to follow.
   End this section by naming the "one big idea."

3. The deep dive (bulk of the post, 3-6 sections)
   Each section: one design decision → code evidence → implication.
   Weave comparison with mainstream approaches naturally — not as a separate section.
   Build sections so each one deepens the previous.

4. What's NOT in it (1-2 paragraphs)
   Deliberate omissions reveal philosophy as much as features do.

5. Why it matters (2-3 paragraphs)
   Zoom back out. Connect the specific tool to a broader trend or principle.
   End with a forward-looking statement, not a summary.
```

Sections 3 is the core. Allocate 60-70% of the post there.

## Code Usage

- Show 3-6 snippets total. Each under 20 lines. Cut imports and boilerplate.
- Introduce code BEFORE showing it: "X solves this by doing Y:" then the snippet.
- After the snippet, explain the non-obvious part only. Do not narrate what the code literally does line by line.
- Use `# ...` to elide irrelevant parts of a function.

## Comparison Technique

Do NOT:
- Write a "Comparison" section with a table
- Say "unlike X which is bad, Y is good"
- Compare more than 2-3 tools in one paragraph

DO:
- Weave comparison into the narrative: "Most agents do X. This one does Y. The trade-off is Z."
- Use specific, concrete differences, not abstract qualities
- Name the mainstream approach, describe it in one sentence, then pivot to the different choice

## Tone Calibration

- OK: "This is an unusual choice." / "I think this matters."
- OK: "Most tools do X. Bub doesn't. Here's why that's interesting."
- Avoid: "This is revolutionary." / "This is clearly superior."
- Avoid: "As we all know..." / "It goes without saying..."
- Avoid: Emoji, exclamation marks, rhetorical questions as section headers

## Length

Target 2000-4000 Chinese characters (excluding code). Shorter is better if the idea is clean.
