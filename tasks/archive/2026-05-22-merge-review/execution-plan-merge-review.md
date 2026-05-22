# Merge Review Skill

Goal: Add a new goal-backed `$merge-review` skill that loops on current-branch merge readiness until no fixable findings remain.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- `$merge-review` should be a new Prime Directive skill.
- The normal invocation should be `/goal $merge-review`.
- The skill should create and maintain a durable state doc while it runs.
- The loop should continue until a fresh branch review finds no remaining fixable merge-readiness findings.
- `$repo-sweep` remains the whole-repo health audit. `$merge-review` is the current-branch merge gate.
- `$ship-branch` remains separate and owns pushing, PR creation, merge, and branch cleanup.

## Steps

### 1. Define the skill contract

Goal: Create a small public skill surface that clearly routes into a long-running goal loop.

- [x] Add a new `skills/merge-review/SKILL.md`.
- [x] Make the public trigger clear: `/goal $merge-review`.
- [x] Say `$merge-review` is for current-branch merge readiness, not whole-repo sweeping or shipping.
- [x] Keep default behavior loop-first, with report-only behavior only if it is needed and does not confuse the normal path.

### 2. Define the durable state document

Goal: Give the goal run a persistent source of truth that survives compaction, restart, and handoff.

- [x] Specify the state doc path as `tasks/merge-review-<branch-slug>.md`.
- [x] Define required sections for branch/base, review scope, end condition, round log, findings, fixes, validation, remaining decisions, residual risks, resume state, and final verdict.
- [x] Make the state doc the source of truth for the loop, with the `/goal` prompt pointing back to it.
- [x] Require the state doc to stay current after every meaningful review, fix, validation, blocker, or resume point.

### 3. Define the end condition

Goal: Make the stop rule strict enough to prevent premature completion without requiring impossible zero-risk certainty.

- [x] Require a fresh full-branch review over `origin/main...HEAD` after the latest fixes.
- [x] Stop only when that fresh review finds no remaining `Disposition: fix` findings.
- [x] Require every earlier `fix` finding to be fixed and validated, or reclassified with evidence.
- [x] Allow remaining findings only when they are `needs human decision`, `residual risk`, or `no action`.
- [x] Require relevant validation to pass, or failures to be recorded as blocked or residual with evidence.
- [x] Require the state doc resume state to say `Current status: done` before completion.

### 4. Define the review loop

Goal: Specify the repeated inspect -> classify -> fix -> validate -> rereview cycle.

- [x] Establish branch scope from the current non-base branch against `origin/main`.
- [x] Inspect changed files, full changed-file contents, and nearby callers or importers when boundaries are touched.
- [x] Review for real bugs, fake completion, shallow abstractions, scattered domain logic, oversized files, weak tests, frontend regressions, and production-readiness gaps when relevant.
- [x] Classify findings as `fix`, `needs human decision`, `residual risk`, or `no action`.
- [x] Fix all clear local `fix` findings with the smallest safe change.
- [x] Run focused validation after fixes, then broader branch-relevant validation when needed.
- [x] Start a fresh rereview after each fix batch and continue until the end condition is met or a real blocker is proven.

### 5. Connect to existing review contracts

Goal: Reuse Prime Directive review rules instead of copying a second large review framework.

- [x] Reuse `review-protocol.md` prompts and finding disposition shape where practical.
- [x] Reuse architecture guidance when the branch is boundary-affecting or `docs/ARCHITECTURE.md` exists.
- [x] Reuse frontend evidence rules when the branch touches UI or interactions.
- [x] Reuse production-readiness checks when the branch touches backend, config, deploy, data, security, tools, or outbound actions.
- [x] Avoid duplicating large review rubrics in the main skill file; put detailed merge-review rubric or state-doc template in a lazy-loaded reference if needed.

### 6. Update public skill metadata and validation

Goal: Make the skill visible and keep public skill contracts consistent.

- [x] Add the new skill to `README.md`.
- [x] Add `skills/merge-review/agents/openai.yaml` if the repo pattern requires it for public skills.
- [x] Update contract ownership only if the new skill owns a reusable contract that other skills will reference.
- [x] Update validators only if the new public skill metadata or modifiers require validator awareness.

### 7. Validate the implementation

Goal: Prove the skill contract and local install are current.

- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.
- [x] Review the final diff to confirm `$merge-review` is a focused branch merge-readiness loop, not a duplicate `$repo-sweep`.
