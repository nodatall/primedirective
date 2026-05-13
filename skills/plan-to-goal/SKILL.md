---
name: plan-to-goal
description: Convert messy source material, a readable execution plan, or PRD/TDD/tasks-plan artifacts into a reviewable `tasks/goal-plan-<plan-key>.md` document with a compact paste-ready `/goal` prompt. Use when work is an adaptive evidence loop where validation results decide the next implementation step.
---

# Plan To Goal Skill

Convert a plan-shaped request into a Codex goal prompt without starting the goal.

This skill drafts only. It does not activate `/goal`, create an active goal, or execute the plan unless the user explicitly says to start it afterward.

## Activation

Invoke explicitly with `$plan-to-goal`.

Required request context:

- `plan-key=<plan-key>` when building from existing PRD/TDD/tasks-plan artifacts and the key cannot be inferred.

Also use this skill when another Prime Directive workflow detects goal-shaped work and needs a goal-plan artifact instead of a normal implementation checklist.

Examples:

- `$plan-to-goal` with a thread plan above it.
- `$plan-to-goal using tasks/execution-plan-badness-prior-v3-recent-training.md`.
- `$plan-to-goal plan-key=<plan-key>` from existing PRD/TDD/tasks-plan artifacts.

## Goal Candidate Test

Prefer a goal plan when any of these are true:

- If validation results decide the next implementation step, prefer a goal plan.
- The work is inspect -> patch -> validate -> inspect again until confidence or a blocker.
- The success condition is proving a path works, exhausting a search space, improving coverage until recoverable options are exhausted, or diagnosing why repeated attempts still fail.
- The plan has a fixed holdout artifact, benchmark, comparator, baseline, ceiling, or target metric that should guide iterative work.

Do not use a goal plan for a straightforward feature, bug fix, copy edit, cleanup, PR response, or one-pass checklist where the final task list is already stable.

## Artifact

Write:

- `tasks/goal-plan-<plan-key>.md`

The goal plan is a review artifact. It must include a compact paste-ready `/goal` prompt and any supporting notes needed for review.

Keep the `/goal` prompt compact. Target roughly 2,800 characters and keep it under 4,000 characters. Put rationale, examples, and long evidence outside the prompt in the surrounding goal-plan doc.

## Weak Goal Gate

Before writing a goal plan, verify that the source has enough shape for autonomous goal work:

- Clear objective.
- Repo path or concrete discovery starting point.
- Baseline, known bad state, or first-loop instruction to measure the baseline.
- Target, comparator, ceiling, or success signal.
- Boundaries, non-goals, or safety constraints.
- Done-when criteria that are measurable.
- Verification command, artifact, or observable behavior.

If any required item is missing, do not write `tasks/goal-plan-<plan-key>.md`. Stop with:

```text
Not goal-ready yet.

Missing:
- <specific missing decision or evidence>

Needed before goal planning:
- <the smallest question or repo check that would close the gap>
```

Ask only for missing information that changes what "done" means, changes safety/scope, or cannot be discovered quickly from the repo.

## Format

Use this shape:

````md
# <Goal Name>

This should run as a Codex `/goal`, not a normal implementation checklist.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

If this looks right, say: `start this as a goal`.
Do not approve this as a normal implementation checklist.

## Goal Prompt

```text
/goal <one sentence objective>

Use <absolute repo path>.

Objective:
<what must become true>

Target and baseline:
- Current baseline: <measured current behavior, score, speed, coverage, failure shape, or known bad state>
- Target: <measurable target, comparator, ceiling, or improvement threshold>
- Work backward from the target when choosing diagnostics and patches.

Work loop:
1. <inspect current evidence or workflow>
2. <make the smallest useful change>
3. <run a repeatable validation or comparison>
4. <inspect whether it worked>
5. <diagnose and patch again until acceptance criteria are met or a clear blocker is proven>

Acceptance criteria:
- <evidence-based stopping rule>
- <validation command or artifact exists>
- <no-go safety boundary>
```

## Why This Is A Goal

- <Why this is adaptive rather than a stable checklist.>

## Starting Evidence

- <Existing plan, run id, artifact, failing behavior, command, benchmark, comparator, ceiling, or target metric.>

## Boundaries

- <What must not change while the goal runs.>

## State Recording

- <Where the goal should record current evidence, blocker, next action, and validation result when the run is long or resume-prone.>
````

## Workflow

1. Establish source material from the thread, pasted source, existing execution plan, repo review, research output, or PRD/TDD/tasks-plan artifacts.
2. Inspect the target repo enough to avoid inventing a goal that ignores obvious local constraints.
3. Inspect `git status --short` before writing files and do not overwrite unrelated changes.
4. Decide whether the source is goal-shaped using the Goal Candidate Test.
5. If it is not goal-shaped, say it should remain a normal execution plan and stop.
6. Run the Weak Goal Gate.
7. If the gate fails, stop with the missing items. Do not write a goal-plan file.
8. Write or update `tasks/goal-plan-<plan-key>.md`.
9. Preserve concrete source constraints: fixed artifacts, commands to reuse, no-new-run requirements, shadow-only boundaries, promotion bans, safety constraints, and stop conditions.
10. Include measurable baseline, target, ceiling, benchmark, or comparator when available. If missing and central to the goal, add a clear first-loop instruction to measure the baseline before optimizing.
11. Keep the embedded `/goal` prompt compact. Put supporting rationale outside it.
12. Refine the goal plan for missing evidence, absent baseline or target metrics, vague stopping rules, unsafe side effects, unclear validation commands, missing state recording, and missing boundaries.
13. Stop for user review. Do not start the goal unless the user explicitly says to start it.

## Examples

- A badness-prior training task that must train on recent V3 artifacts, score a fixed holdout run, inspect whether score spread improved, and then diagnose or patch again if the scores stay collapsed is a goal candidate.
- A performance goal that names current throughput, a hardware ceiling, and a known comparator should tell the agent to calculate the plausible maximum, measure the current baseline, and work backward from the target.
