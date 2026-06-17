# Backend Optimizer Skill

Goal: Add a Prime Directive `$backend-optimizer` skill for goal-loop backend and database performance work.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The skill should be goal-friendly: `baseline -> inventory -> rank -> experiment or fix -> verify -> resweep -> closeout`.
- The core modes are `--query-sweep`, `--schema-health`, `--runtime`, and `--ops-hygiene`.
- Do not include a `--hot-path <route-or-job>` mode in this skill.
- Do not include a `--redesign` mode. Larger schema or backend redesign proposals belong in `$repo-sweep`, `$create-architecture`, or normal planning workflows.
- The skill should use a candidate ledger so the loop can stop cleanly instead of chasing endless possible improvements.

## Steps

### 1. Define the skill contract

Goal: Make the public behavior clear before writing workflow details.

- [x] Add a new Prime Directive skill named `backend-optimizer`.
- [x] Initialize or create the skill folder using the local skill-authoring guidance, while matching the existing Prime Directive `skills/<skill-name>/SKILL.md` layout.
- [x] Define activation for explicit `$backend-optimizer` usage and `/goal $backend-optimizer` usage.
- [x] Define bare `$backend-optimizer` as report-first: inventory, rank, and recommend optimizations, then stop before code, schema, config, or migration changes unless the user explicitly approves fixes.
- [x] Define `/goal $backend-optimizer` as the bounded measured fix loop for safe candidates, while preserving human approval gates for risky decisions.
- [x] Define supported modes: `--query-sweep`, `--schema-health`, `--runtime`, and `--ops-hygiene`.
- [x] State that safe, measured fixes can be implemented during goal loops, while risky schema, product, data-loss, public API, security, billing, or deployment decisions must stop for human approval.
- [x] State that broad redesign findings should be reported as gated findings and routed to `$repo-sweep`, `$create-architecture`, or a separate approved plan.

### 2. Specify the shared goal loop

Goal: Give every mode the same evidence-driven loop and stop condition.

- [x] Document the shared loop: baseline, inventory, rank candidates, experiment or fix, verify, resweep, and close out.
- [x] Define the candidate ledger shape: candidate, evidence, proposed fix, experiment, result, disposition, validation, and next action.
- [x] Define where the candidate ledger and resume state live during `/goal $backend-optimizer` runs, preferring goal state plus a repo-local `tasks/tmp/backend-optimizer-<mode>-ledger.jsonl` artifact when that directory exists.
- [x] Require the ledger or goal state to be updated after each candidate is classified, fixed, rejected, or gated, so interruption or context compaction has a clear resume point.
- [x] Define dispositions: `improved`, `already acceptable`, `not worth cost`, `unsafe without approval`, `blocked by missing realistic data`, `requires product/schema decision`, and `failed experiment`.
- [x] Define the stop condition: every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision.
- [x] Require before/after evidence for any claimed optimization.

### 3. Define mode-specific checks

Goal: Keep the modes focused and avoid turning the skill into a generic repo sweep.

- [x] For `--query-sweep`, require query inventory, ranking by measured impact, query plans or equivalent evidence, safe query/index experiments, and before/after verification.
- [x] For `--schema-health`, review tables, indexes, constraints, foreign keys, duplicate or unused indexes, growth risks, and data-shape issues that affect reliability or performance.
- [x] For `--runtime`, inspect backend code paths beyond the database: serial awaits, repeated initialization, blocking I/O, large responses, expensive serialization, caching opportunities, and unnecessary repeated work.
- [x] For `--ops-hygiene`, inspect connection pooling, timeouts, lock risk, migration safety, vacuum/analyze or bloat signals, slow-query visibility, observability, and alerting gaps.
- [x] Keep each mode tied to concrete backend or database performance evidence, not broad maintainability cleanup.

### 4. Add references only where they reduce context cost

Goal: Keep `SKILL.md` concise while preserving useful detail.

- [x] Decide whether mode details should live in `SKILL.md` or one-level reference files under `skills/backend-optimizer/references/`.
- [x] If references are useful, add only the files needed for the four modes and make `SKILL.md` say exactly when to read each one.
- [x] Reuse existing shared review, verification, and architecture guidance by reference instead of duplicating it.
- [x] Do not add scripts unless implementation shows a repeated deterministic probe is worth owning in this repo.

### 5. Make the skill discoverable

Goal: Wire the new skill into the Prime Directive public surfaces.

- [x] Add the skill to the README skill quick reference table.
- [x] Add a short README detail section that explains when to use `$backend-optimizer` instead of `$repo-sweep`.
- [x] Leave launcher metadata out unless implementation finds a current Prime Directive convention that requires it.
- [x] Update contract ownership or validator expectations only for durable workflow contracts that this skill owns.

### 6. Validate the skill change

Goal: Prove the local install and skill contract are current.

- [x] Run `/Users/fromdarkness/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/backend-optimizer` through `python3` with PyYAML available. If the local Python lacks PyYAML, use a temporary `/private/tmp` dependency target instead of changing the global Python environment.
- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.
- [x] Inspect `git status --short` and confirm only intended files changed.
