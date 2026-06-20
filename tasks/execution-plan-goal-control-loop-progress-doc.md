# Goal Control Loop Progress Doc

Goal: Make `/goal` plans explicitly describe their control loop and require a progress document before the goal starts.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The user wants to skip automation-specific fields for now.
- Every `/goal` plan must include an explicit `Progress Document` field before work starts.
- For ordinary goals, the `Progress Document` is the current goal plan's `Resume State` section; this default must be written in the plan, not merely implied.
- Specialized skills may name stronger progress records, such as a goal-state document plus JSONL ledger.
- The goal must not start if `Progress Document` is missing, placeholder-only, or not tied to a document or document section.
- The goal must not count as complete if the named progress document is missing, stale, or lacks the next exact action or a terminal-complete note with the final verifier result.

## Decisions From Research

- `skills/plan-to-goal/SKILL.md` is the owner for the full control-loop and progress-document rule.
- `$deliver`, README, and contract ownership should only get short mirrors when needed; they should not duplicate the whole goal contract.
- Automation-only fields stay out of this change: triggers, retries, on-failure hooks, run history dashboards, hot deploys, concurrency controls, and owner/disable controls.
- Validator coverage is required so the owner wording and mirrors cannot drift silently.

## Steps

### 0. Inventory Existing Goal Entrypoints And Mirrors

- [ ] Capture initial `git status --short --branch`.
- [ ] Search for `/goal`, `plan-to-goal`, `Resume State`, `Work Loop`, `Stop Conditions`, `Start Prompt`, `PD-PLAN-TO-GOAL`, `PD-DELIVER-GOAL-PLAN`, and README goal-skill mirror wording.
- [ ] Classify each relevant hit as owner, mirror, template, prompt, validator, or no-change.
- [ ] Do not update automation or orchestrator-layer wording except to preserve the explicit deferral.

### 1. Strengthen The Goal Contract

- [ ] Update `skills/plan-to-goal/SKILL.md` so every goal plan must include a `Control Loop` section with `Current State`, `Desired End State`, `Incremental Change Rule`, `Primary Verifier`, `Stop Conditions`, and `Progress Document`.
- [ ] Define `Progress Document` as an explicit non-placeholder reference to the document or document section where progress is saved.
- [ ] Set the default ordinary-goal value to `Progress Document: This goal plan's Resume State section`.
- [ ] Add a start gate: do not start goal execution until `Progress Document` is present and names either the goal plan's `Resume State` section or a stronger specialized progress record.
- [ ] Add completion wording: a goal is not complete unless the named progress document is current after the final verifier and contains either the next exact action or an explicit terminal-complete note with the final verifier result.
- [ ] Update the goal-plan template with the `Control Loop` fields and a `Resume State` shape that records last meaningful checkpoint, last verified state, next exact action, and open risks or blockers.
- [ ] Update start-prompt wording so the agent keeps the named progress document current after meaningful checkpoints and before any stop, handoff, or completion claim.
- [ ] Inspect `skills/plan-to-goal/agents/openai.yaml`; update it if it contains default goal-start instructions, otherwise record the no-change rationale in the implementation summary.

### 2. Update Consumers And Guardrails

- [ ] Add a short `$deliver` goal-delegation pointer: for `/goal`-shaped work, delegate to `$plan-to-goal`; the approved goal plan must define a control loop and explicitly name its `Progress Document` before implementation starts.
- [ ] Inspect `README.md`; if it summarizes `$plan-to-goal` or `/goal`, add a short mirror saying goal plans must define a control loop and name a progress document. If not, record the no-change rationale in the implementation summary.
- [ ] Inspect `skills/shared/references/contract-ownership.md`; if it lists goal-plan or state-recording ownership, update the `plan-to-goal` row to name the control-loop and progress-document contract. If not, record the no-change rationale in the implementation summary.
- [ ] Update `scripts/validate-skill-contracts.py` so drift is caught for the owner rule, template fields, start gate, completion gate, and any `$deliver`/README/contract-ownership mirrors.
- [ ] Validator checks should include the required concepts: `Control Loop`, `Current State`, `Desired End State`, `Incremental Change Rule`, `Progress Document`, `Resume State`, "before work starts", and the completion rule for missing or stale progress records.

### 3. Validate The Contract Change

- [ ] Run `python3 scripts/validate-skill-contracts.py`.
- [ ] Run `git diff --check`.
- [ ] Run `./scripts/install-codex-plugin.sh`.
- [ ] Manually smoke-check the resulting goal-plan template: confirm a newly drafted `/goal` plan cannot omit the control-loop fields or explicit `Progress Document`.
- [ ] Perform a final adversarial pass: try to find any path where `/goal` can start without a named progress document, complete with stale progress, or introduce deferred automation/orchestrator fields.
- [ ] Check `git status --short --branch` and summarize any remaining dirty files.

## Acceptance Criteria

- `skills/plan-to-goal/SKILL.md` is the single owner of the full `/goal` control-loop and progress-document contract.
- Every generated `/goal` plan has explicit fields for current state, desired end state, incremental change rule, verifier, stop condition, and progress document.
- Every generated `/goal` plan explicitly names where progress is saved, even when the answer is the goal plan's own `Resume State` section.
- A goal cannot start with a missing or placeholder-only `Progress Document`.
- A goal cannot be marked complete with a missing, stale, or non-actionable progress document.
- `$deliver`, README, and contract ownership contain only short mirrors or no-change rationale; they do not duplicate the full goal contract.
- No trigger, retry, owner/disable, run-history dashboard, concurrency, hot-deploy, or other orchestrator-layer fields are added.
