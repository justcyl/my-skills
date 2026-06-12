# Anti-Fable Skill

Anti-Fable is a cross-domain explanation skill. It turns dense technical, scientific, policy, systems, or safety-sensitive questions into fables that non-specialists can understand while preserving the original structure, constraints, causal relationships, and uncertainty.

## Good Uses

- Explain a complex research question to a non-specialist audience.
- Turn a paper, proposal, mechanism, or debate into a story that is easier to retell.
- Produce two versions: one plain and direct, one more atmospheric and image-rich.
- Reduce dependence on jargon so the discussion can focus on the underlying structure.

## Poor Uses

- Hiding harmful intent, evading platform safety checks, or disguising disallowed operational guidance as a story.
- Preserving exact formulas, citations, proper nouns, parameters, or executable steps.
- Replacing legal, medical, financial, or other professional judgment. The skill can explain concepts in plain language, but it cannot supply professional advice.

## How It Works

Give the model the original question or material and ask it to use Anti-Fable. By default, it returns:

1. `Plain Fable`: a clear, direct fable.
2. `Image-Rich Fable`: a richer version with more atmosphere and imagery.
3. `Fidelity Check`: a source-domain-neutral note on the core structure, constraints, and confidence conditions preserved by the fables.

The skill privately abstracts the structure of the problem, then chooses a story world far away from the source domain. It does not output a mapping table by default; ask for author notes separately if you need one.

## Safety Boundary

Anti-Fable is for explanation, teaching, creative reframing, and structured reasoning. It should not convert unsafe requests into indirect tutorials or hide the user's underlying intent to pass a filter. If the original request is harmful, refuse or redirect to a safe high-level explanation before writing a fable.
