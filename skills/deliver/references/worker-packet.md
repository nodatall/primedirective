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

Rules:
- Do not edit outside this step unless required and reported.
- Do not mark other plan items done.
- Do not commit.
- Return changed files, validation run, result, and blockers.
```

The orchestrator keeps ownership of the full plan, next-step selection, worker packet creation, worker integration, final validation judgment, checkbox updates, commits, and plan changes. It should not hand a worker the whole backlog or ask the worker to choose the next item.
