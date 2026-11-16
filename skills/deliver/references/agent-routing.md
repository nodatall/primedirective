# Deliver Agent Routing

Read this before every Deliver subagent assignment, including discovery, plan refinement, implementation, repair, and final review. Choose settings for the actual task; do not reuse the previous worker's route without checking it. This file owns Deliver's model and reasoning selection. Existing plan, approval, context, validation, and review-topology requirements still apply.

Invoking Deliver authorizes choosing each subagent's model and reasoning effort within the available runtime and the user's explicit model, provider, or budget constraints. Keep the parent chat's model unchanged. Do not edit global defaults or custom-agent configuration to accomplish routing.

## Discover Current Options

At the first assignment in a run, inspect the live agent tool's model catalog, supported reasoning levels, context modes, and override restrictions. Use current runtime metadata or authoritative provider documentation when capability information is needed. Reuse this inventory during the run and refresh it after an availability or unsupported-setting error.

Map available models to useful capability classes: fast economical work, general coding and tool use, and strong reasoning. Choose by documented capabilities, required tools and context capacity, and the task's uncertainty and consequences. Neither a newer name nor a higher version number proves that a model fits a role. New models can fill these classes without changing this contract; never invent an identifier, reasoning level, capability, or price.

If no catalog or capability information is exposed, use a known suitable allowed model or inherited settings conservatively. Record that limitation rather than guessing a cheaper model. A model being available does not waive the user's constraints.

## Route By Difficulty And Role

Prefer an efficient available model that can meet the task's capability needs. File count and prompt length are not difficulty measures.

| Assignment | Model capability | Starting reasoning |
| --- | --- | --- |
| Mechanical edits, explicit copy or spacing replacements, deterministic checks, or bounded read-only extraction with an obvious pattern | Fast economical | `medium`, or the closest supported standard level |
| Scoped implementation or investigation with clear behavior, local patterns, and acceptance criteria | General coding and tool use | `medium`; increase to `high` when meaningful logic or edge cases require it |
| Ambiguous debugging, design judgment, integration behavior, security, public contracts, data integrity, migrations, concurrency, or substantive plan refinement and review | Strong coding or reasoning | `high`, or the closest supported strong level |
| Difficult unresolved diagnosis, deep research or first-principles challenge, repeated review churn, or recovery after a capability-related failure | Strong reasoning appropriate to the unresolved problem | A supported level above `high`, such as `xhigh`, when available and justified |

Treat initial final review and substantive repair rereview as strong reasoning assignments even when the patch is small. Preserve any stronger model or reasoning requirement imposed by a requested specialist workflow. Use the strongest appropriate review setting within the user's constraints; do not route final review to a cheap mechanical worker. A one-line authorization change or an unexplained UI regression belongs on the strong route.

When uncertainty prevents a responsible implementation assignment, inspect the relevant evidence or assign bounded discovery first. Reassess the implementation route from what it finds. Keep the parent responsible for integration and verification; do not lower the verification bar to fit a cheaper worker.

## Apply The Selection

Record the role, difficulty, exact model, supported reasoning effort, context mode, and one-sentence selection reason in the implementation packet or the existing brief for another agent role. Routing metadata stays out of the approved plan's high-level checkboxes. The actual spawn request must match the recorded selection; describing a worker as “high reasoning” in prose does not set its reasoning level.

With `collaboration.spawn_agent`, per-agent overrides use `model` and `reasoning_effort` together with `fork_turns: "none"`. That worker receives no conversation history: provide a self-contained brief with the approved task, necessary decisions and constraints, absolute repo path, applicable instructions, relevant artifacts, ownership, and required evidence. The implementation packet supplies its task-specific context. Give reviewers the full required review scope, plan, linked notes, and diff context; routing must not compress away required review evidence.

In that tool, omitting `fork_turns` or using `"all"` inherits the parent's model and reasoning and disallows overrides. When full-history inheritance is necessary, omit overrides and record the actual route as inherited. Other hosts may expose different options; use their current schema rather than assuming these argument names work everywhere. If an effective setting is pinned by a custom agent, respect it and do not claim a requested override took effect.

If a selected model or level becomes unavailable, choose another supported route that meets the capability floor and user constraints. If overrides are unavailable, use supported inheritance and record the limitation. If delegation itself is unavailable, follow Deliver's local-execution fallback. Do not present inherited or unverified settings as a successful model switch.

Model selection does not change ownership or concurrency: implementation workers remain sequential, and fresh reviewers remain independent siblings of implementation workers. Use follow-up messages to steer an existing worker; changing its model requires a new assignment when the tool has no setting-change operation.

## Escalate From Evidence

After a failure, distinguish an unavailable setting, missing permission or environment, unresolved product decision, and a reasoning or implementation failure. More reasoning cannot supply credentials or authorization. Address the actual blocker before retrying.

Escalate a fast worker's unresolved slice when it encounters material ambiguity, expands beyond its packet, or fails focused verification because of a capability-related mistake. Preserve useful edits and pass the failure evidence to the stronger worker. End or interrupt the previous assignment before transferring ownership, and do not run competing repairs or repeatedly retry the same cheap route. Recheck scope and the failure mechanism before any further escalation; stop when progress requires a user decision or external change. All existing Deliver stop conditions remain in force.
