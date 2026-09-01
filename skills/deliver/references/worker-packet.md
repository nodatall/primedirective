# Deliver Worker Packet

Read this before assigning a non-trivial `$deliver` implementation item.

Give the worker one bounded item and only the context needed for it:

```md
# Active Step Packet

Plan: tasks/execution-plan-<plan-key>.md
Step: <exact phase and checkbox text>

Goal:
<one sentence from the plan when useful>

Do:
<the one checkbox or item this worker owns>

Done when:
<include only when the checkbox is not enough>

Relevant context:
- <only facts or decision notes needed for this step>
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
- Rationale: <why durable coverage is justified, or why it is not>

Rules:
- Do not edit outside this step unless required and reported.
- Do not mark other plan items done.
- Do not commit.
- Return changed files, validation run, result, and blockers.
```

The orchestrator chooses the item, writes the packet, integrates the change, judges validation, updates the plan, commits, and changes scope when evidence requires it. The worker receives one item, not the backlog.

When tests may change, the orchestrator decides `test_disposition` and writes its evidence-backed rationale before assigning permanent-test work. If the evidence is not yet enough, assign only reproduction or repair. Decide test persistence after inspecting the result.

For a parser or validator repair, make `Validation` test accepted-looking values against the downstream consumer grammar, not only the repaired guard.

For an approved cross-process lifecycle repair, make `Validation` cover synchronous completion after an intermediate readiness signal, concurrent waiters, the active owner or lock, failed or stale owner recovery, and default-versus-foreground behavior.

Keep disposable or historical checks as `probe_only`. Do not invent a permanent harness or expand the approved behavior merely to satisfy a check.
