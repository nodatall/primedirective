---
name: plan-to-goal
description: Convert messy source material, a readable execution plan, or PRD/TDD/tasks-plan artifacts into a reviewable `tasks/goal-plan-<plan-key>.md` document, then print a separate compact paste-ready `/goal` prompt that references that file. Use when work is an adaptive evidence loop where validation results decide the next implementation step.
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

Use a goal plan only when the source is open-ended enough that a stable checklist would be dishonest and the agent can run a real adaptive loop inside the goal.

Goal plans require a real adaptive loop:

- If validation results decide the next implementation step, prefer a goal plan.
- The work is inspect -> patch -> validate -> inspect again until confidence or a blocker.
- The success condition is proving a path works, exhausting a search space, improving coverage until recoverable options are exhausted, or diagnosing why repeated attempts still fail.
- The plan has a fixed holdout artifact, benchmark, comparator, baseline, ceiling, or target metric that should guide iterative work.

Goal mode also requires feedback cadence that fits autonomous iteration. Do not use a goal plan when the decisive evidence comes mainly from a slow, paid, approval-gated, nightly, or externally scheduled run that the agent cannot repeat several times before the next operator decision. In that case, write a normal execution plan or tasks plan that builds the harness, proves the plumbing with cheap checks, and prepares the one decision run for human approval.

Do not use a goal plan for a straightforward feature, bug fix, copy edit, cleanup, PR response, one-pass checklist, or experiment setup where the implementation work is nameable and the main unknown is what a later operator-approved run will show.

When the source is ambiguous, default to normal planning. Convert to a goal plan only when the plan cannot honestly name the remaining implementation steps until after the next validation result and that validation loop is practical to run repeatedly inside the goal.

AutoProphet example:

- Goal candidate: "Keep diagnosing and patching the badness-prior training path using existing artifacts and a fixed holdout comparison until score collapse is fixed or a blocker is proven."
- Not a goal candidate: "Design and build the R1 multi-arm probe, prove arm tagging and budgets with cheap offline/smoke checks, then prepare one paid 2-4 hour decision run for approval before the next nightly."

## Artifact

Write:

- `tasks/goal-plan-<plan-key>.md`

The goal plan is a review artifact and source-of-truth context file. It must not embed the full `/goal` prompt. It should contain the objective, evidence, loop rules, acceptance gates, resume state, and boundaries the user needs to review before the goal starts.

After writing or updating the goal plan, print the compact paste-ready `/goal` prompt separately in the chat response. The prompt must reference the absolute path to `tasks/goal-plan-<plan-key>.md` and tell the goal agent to read that file as the source of truth. Keep the `/goal` prompt compact. Target roughly 900 characters and keep it under 4,000 characters. Put rationale, examples, and long evidence in the goal-plan doc, not in the chat prompt.

Every goal plan must include a `Resume State` section that gives the next agent one obvious place to resume from after compaction, interruption, or handoff.

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

## How To Start This Goal

When this looks right, the agent should print a separate paste-ready `/goal` prompt in chat. That prompt must reference this file by absolute path instead of duplicating the plan text.

Do not copy this Markdown file into `/goal`.

## Why This Is A Goal

- <Why this is adaptive rather than a stable checklist.>

## Starting Evidence

- <Existing plan, run id, artifact, failing behavior, command, benchmark, comparator, ceiling, or target metric.>

## Target and baseline:

- Current baseline: <measured current behavior, score, speed, coverage, failure shape, or known bad state>
- Target: <measurable target, comparator, ceiling, or improvement threshold>
- Work backward from the target when choosing diagnostics and patches.

## Work Loop

1. <inspect current evidence or workflow>
2. <make the smallest useful change>
3. <run a repeatable validation or comparison>
4. <inspect whether it worked>
5. <diagnose and patch again until acceptance criteria are met or a clear blocker is proven>

## Acceptance Criteria

- <evidence-based stopping rule>
- <validation command or artifact exists>
- <no-go safety boundary>

## Resume State

- Current status: todo
- Current phase: <not started, investigating, patching, validating, blocked, or done>
- Last completed step: <what is already finished and validated, or none yet>
- Active step: <what is currently being worked on, or none yet>
- Next exact action: <the next command, file, artifact, or decision to inspect>
- Blockers: <none, or exact blocker and required user/external action>
- Last validation: <command, artifact, or observable result, or none yet>
- Protected paths: <files, directories, data, branches, or services the goal must not touch>
- Evidence paths: <logs, screenshots, reports, temp files, or artifacts that matter for resuming>

## Boundaries

- <What must not change while the goal runs.>
````

## Workflow

1. Establish source material from the thread, pasted source, existing execution plan, repo review, research output, or PRD/TDD/tasks-plan artifacts.
2. Inspect the target repo enough to avoid inventing a goal that ignores obvious local constraints.
3. Inspect `git status --short` before writing files and do not overwrite unrelated changes.
4. Decide whether the source is goal-shaped using the Goal Candidate Test.
5. If it is not goal-shaped, stop without writing a goal plan and name the blocking reason briefly.
6. Run the Weak Goal Gate.
7. If the gate fails, stop with the missing items. Do not write a goal-plan file.
8. Write or update `tasks/goal-plan-<plan-key>.md`.
9. Preserve concrete source constraints: fixed artifacts, commands to reuse, no-new-run requirements, shadow-only boundaries, promotion bans, safety constraints, and stop conditions.
10. Include measurable baseline, target, ceiling, benchmark, or comparator when available. If missing and central to the goal, add a clear first-loop instruction to measure the baseline before optimizing.
11. Print the separate `/goal` prompt in chat after the file is written. The prompt should name the absolute goal-plan path, tell the agent to use the file as source of truth, and stay compact.
12. Fill `Resume State` with the initial status, current phase, next exact action, blockers, last validation, protected paths, and evidence paths. Use `none yet` only when that is true.
13. Refine the goal plan for missing evidence, absent baseline or target metrics, vague stopping rules, unsafe side effects, unclear validation commands, weak resume state, and missing boundaries.
14. Stop for user review. Do not start the goal unless the user explicitly says to start it.

Separate chat prompt shape:

```text
/goal <one sentence objective>

Use <absolute repo path>.

Read <absolute repo path>/tasks/goal-plan-<plan-key>.md first and treat it as the source of truth for objective, target and baseline, work loop, acceptance criteria, evidence paths, Resume State, and boundaries.

Keep the `Resume State` section in that goal plan current after meaningful checkpoints.
```

## Examples

- A badness-prior training task that must train on recent V3 artifacts, score a fixed holdout run, inspect whether score spread improved, and then diagnose or patch again if the scores stay collapsed is a goal candidate.
- A performance goal that names current throughput, a hardware ceiling, and a known comparator should tell the agent to calculate the plausible maximum, measure the current baseline, and work backward from the target.
