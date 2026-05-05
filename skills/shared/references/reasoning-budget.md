# Reasoning Budget Guidance

Use phase-appropriate model and reasoning settings. Every skill run should choose deliberately by role, while staying within the user's selected model family or budget unless they explicitly authorize changing it.

- Planning, plan refinement, and final review: start with a strong reasoning setting that is appropriate for the user's selected model family or budget.
- Deep research, first-principles audit, unresolved blocker analysis, repeated review churn, and prior-pass failure recovery: escalate to the strongest available reasoning setting.
- Implementation and build workers: use strong reasoning, usually one tier below escalated research and review work.
- Mechanical chores such as formatting, file moves, narrow command checks, simple cleanup, deterministic verification, and artifact archival: use standard or medium reasoning.
- One-shot implementation worker model routing may use a fast coding model only for packets explicitly marked `worker_model_tier: spark_candidate` by `skills/shared/references/execution/task-management.md`.

Treat reasoning effort as a last-mile knob, not the primary quality lever. Prefer clearer task contracts, explicit completion criteria, tool persistence rules, and targeted verification before escalating routine planning or review work to the maximum tier.

Do not hardcode this guidance to a single provider or model name. When spawning or delegating to subagents, request the reasoning tier by role: high for routine planning, refinement, and final review; highest for deep research, first-principles audit, unresolved blockers, repeated churn, and failed prior passes; high for implementation workers; medium for mechanical work.

Exception: when a one-shot worker packet is marked `worker_model_tier: spark_candidate`, OpenAI/Codex workers may use `gpt-5.3-codex-spark` or the closest available fast coding model. Claude users should ignore this as a model-selection directive unless their environment has an explicitly configured equivalent fast worker model. The main orchestrator and final review must not be downgraded by this worker-level routing.

For OpenAI/Codex-style reasoning tiers, map the roles as:

- routine planning, refinement, and final review: `high`
- deep research, first-principles audit, unresolved blocker analysis, repeated review churn, and prior-pass failure recovery: `xhigh`
- implementation and build workers: `high`
- mechanical chores and deterministic verification: `medium`

When exact tier names differ in another runtime, use the closest equivalent relative tiers rather than changing the workflow shape.
