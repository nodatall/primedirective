# Reasoning Budget Guidance

Use phase-appropriate model and reasoning settings. Every skill run should choose deliberately by role, while staying within the user's selected model family or budget unless they explicitly authorize changing it.

- Planning, plan refinement, deep research, first-principles audit, and final review: use the strongest available reasoning setting that is appropriate for the user's selected model family or budget.
- Implementation and build workers: use strong reasoning, usually one tier below planning and review.
- Mechanical chores such as formatting, file moves, narrow command checks, simple cleanup, deterministic verification, and artifact archival: use standard or medium reasoning.

Do not hardcode this guidance to a single provider or model name. When spawning or delegating to subagents, request the reasoning tier by role: highest for planning, refinement, deep research, first-principles audit, and final review; high for implementation workers; medium for mechanical work.

For OpenAI/Codex-style reasoning tiers, map the roles as:

- planning, refinement, deep research, first-principles audit, and final review: `xhigh`
- implementation and build workers: `high`
- mechanical chores and deterministic verification: `medium`

When exact tier names differ in another runtime, use the closest equivalent relative tiers rather than changing the workflow shape.
