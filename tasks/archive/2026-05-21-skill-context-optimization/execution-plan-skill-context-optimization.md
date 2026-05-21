# Skill Context Optimization

Goal: Make Prime Directive skills lighter to load without weakening their safety gates or changing their public behavior.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The current rule already lives in `contract-ownership.md`: contracts should have one owner, and consumers should only carry short summaries.
- The change should clarify that rule, not create a competing AGENTS rule.
- `$deliver`, `$repo-sweep`, and `$plan-refine` are the largest skill files.
- `$plan-refine` owns validator-sensitive schema and stamp text, so it should not be split unless ownership and validator checks move with it.
- `AGENTS.md` has a pre-existing dirty change from the earlier `DESIGN.md` rule; keep it separate unless the user asks to include it.

## Steps

### 1. Clarify the skill-authoring rule

Goal: Make the existing ownership rule say what belongs in `SKILL.md` versus reference files.

- [x] Update contract ownership guidance so `SKILL.md` owns activation, routing, and the main workflow.
- [x] Say heavy checklists, templates, rubrics, schemas, and edge-case detail should live in reference files loaded only when needed.
- [x] Keep this framed as a clarification of the one-owner rule.

### 2. Make reference loading more conditional

Goal: Stop skills from implying that every reference must be loaded at startup.

- [x] Update `$plan-work` reference loading so `--deep-research`, Socratic planning, harness drift, and plain-language detail are loaded only on the paths that need them.
- [x] Check `$plan-and-execute` and `$execute-task` for the same issue, and only change wording that clearly over-loads references too early.

### 3. Split bulky `$deliver` detail without changing behavior

Goal: Keep `$deliver` focused on draft -> refine -> approve -> implement.

- [x] Move draft and execution-plan format detail into a `$deliver` reference file.
- [x] Move worker packet detail into a `$deliver` reference file.
- [x] Preserve validator-required wording in the skill, or update the validator in the same change.

### 4. Split bulky `$repo-sweep` detail without weakening review

Goal: Keep `$repo-sweep` focused on detect -> report -> approve or loop -> fix -> resweep.

- [x] Move high-risk checks, go-live readiness checks, and report section detail into repo-sweep reference files.
- [x] Keep `--loop`, `--swarm`, `--dep-scan`, and `--pro-analysis` behavior explicit in the main skill.
- [x] Load detailed `--loop`, `--swarm`, and `--dep-scan` references only on those paths.

### 5. Clean up orchestration duplication

Goal: Keep orchestration skills thin and owned contracts in their owner files.

- [x] Tighten `$plan-and-execute` where it repeats child workflow details instead of pointing to the child owner.
- [x] Keep branch/PR defaults and combined-workflow gates in `$plan-and-execute`.
- [x] Do not weaken final review, archive, commit, or finalization gates.

### 6. Validate and reinstall

- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.
- [x] Review the final diff to confirm this is a context-loading cleanup, not a behavior rewrite.
