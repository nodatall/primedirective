# Deliver Worker Packet

Use this reference before assigning a non-trivial `$deliver` implementation item to a worker agent.

Pass one bounded item with only the context needed to implement it correctly:

```md
# Active Step Packet

Plan: tasks/execution-plan-<plan-key>.md
Step: <exact phase and checkbox text>

Goal:
<one sentence from the plan when useful>

Do:
<the one checkbox/item this worker owns>

Done when:
<include only when the checkbox text is not enough>

Relevant context:
- <only useful What We Know or Decision notes for this step>
- <important constraints from the approved plan>

Repo context:
- Current branch:
- Relevant files or surfaces to inspect first:
- Existing local pattern to follow:
- Unrelated dirty files to avoid:

Validation:
- Focused command or flow to run:
- UI/app inspection needed: yes/no

Test value when this step adds or changes tests:
- test_disposition: permanent | table_case | probe_only | no_test
- Rationale: <why this is supported-path, material, unique, stable, and economical, or why durable coverage is not justified>

Rules:
- Do not edit outside this step unless required and reported.
- Do not mark other plan items done.
- Do not commit.
- Return changed files, validation run, result, and blockers.
```

The orchestrator keeps ownership of the full plan, next-step selection, worker packet creation, worker integration, final validation judgment, checkbox updates, commits, and plan changes. It should not hand a worker the whole backlog or ask the worker to choose the next item.

For a test-changing step, the orchestrator must decide and include `test_disposition` plus its rationale before assigning permanent-test work. When evidence is insufficient to decide, assign only reproduction or repair, keep permanent-test work out of the packet, and decide test persistence after inspecting the evidence.

When a step repairs a parser or validator, put a focused check under `Validation` that exercises accepted-looking values against the downstream consumer grammar, not only the repaired guard. When a step repairs an approved cross-process lifecycle, include synchronous completion after intermediate readiness, concurrent waiters, the active owner or lock, failed or stale owner recovery, and default-versus-foreground behavior. Keep disposable or historical checks as probes rather than inventing a permanent harness, and do not expand the approved behavior contract merely to satisfy the checks.
