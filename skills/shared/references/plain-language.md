# Plain-Language Output

Use this reference when a skill needs a plain, short, user-facing explanation.

## Standard

Explain the idea in the simplest correct way.

- Lead with the main point.
- Use short full sentences.
- Prefer concrete words over abstract labels.
- Avoid jargon unless it is required for correctness.
- When jargon is required, define it in plain words.
- Use exact numbers when they matter.
- Do not add a framework, template, or section stack unless the user asked for depth.
- Do not mention this reference or the plain-language skill in the answer.

## Default Shape

For a quick explanation:

- write 2-5 sentences
- put each sentence on its own line when the user asked for a plainer rewrite
- avoid bullets unless the user asked for them or the answer is easier to scan as a list

For a deeper analysis:

- open with a short plain-language verdict
- add the mechanism after the verdict
- add technical detail only where it changes the decision, confidence, or next step

## Rewrite Rule

If the user asks for `plainer`, `shorter`, `plain language`, or `full sentences`, remove one more layer of abstraction.

Bad:

> The bottleneck is scheduler-level preemption caused by shared dirty-state semantics.

Plain:

> The system keeps choosing to scan the repo again.
> It should spend that time filling the missing PRs instead.

Bad:

> The architectural direction is to decouple canonical object identity from mutable lookup surfaces.

Plain:

> The permanent ID should be the real identity.
> The name is allowed to change.
