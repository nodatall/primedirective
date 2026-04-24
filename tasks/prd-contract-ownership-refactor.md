# Contract Ownership Refactor PRD

## Plain-Language Summary

Prime Directive skills should stop copying the same workflow rules in several places. Each important rule should have one home, and other skills should point to that home instead of restating it.

This work keeps the public skill names and workflows the same. It changes how the repo is written so future edits are less likely to leave stale duplicated instructions behind.

The work is done when the repo has a clear contract-ownership convention, the most drift-prone duplicated docs are reduced or routed to their owner, and validation catches obvious stale mirrors before a PR lands.

## Target User / Audience

The audience is the Prime Directive maintainer and future implementation agents editing this repository. They need skill docs that are easy to update without silently changing the same rule in multiple files.

## Problem Statement

The repository currently repeats workflow contracts across public skill files and shared references. That repetition helped while the workflow was evolving, but it now creates drift risk: a rule can be changed in one place while an older mirror remains elsewhere.

## Current-State / Product Diagnosis

The repo is small enough to fix this in one cohesive pass. It is not large enough to justify a separate public "graph audit" skill or a long incremental migration plan.

Recent workflow edits already exposed the risk: retention and refinement behavior can be changed in one shared reference while another file continues describing the older behavior. The docs need a visible ownership model and a lightweight validation command that catches the easiest stale mirror classes.

## Product Goal

Make Prime Directive skill authoring more maintainable by establishing one owner per workflow contract, reducing duplicate restatements, and adding a repo-local validator that fails when public skill metadata or known contract mirrors drift.

## Success Criteria

- A maintainer can identify the owner file for each major Prime Directive workflow contract.
- The minimum owner inventory covers activation/path contracts, plan-work, plan-refine challenger behavior, execute-task one-shot behavior, finalization, review protocol, deep research, Pro analysis, task management, harness drift, reasoning budget, and public README skill metadata.
- Higher-level skills read as orchestrators and reference lower-level contracts instead of restating detailed child behavior.
- Remaining mirrors are intentionally small summaries, not parallel contracts.
- CI runs a contract validator in addition to existing installer validation.
- No public skill invocation names, modifiers, or intended user-facing workflows change.

## Explicit Non-Goals

- Do not add a new public graph-audit, contract-audit, or skill-graph skill.
- Do not introduce a dense dependency graph or runtime skill router.
- Do not sync changes into downstream consumer repos.
- Do not rename existing public skills or remove supported modifiers.
- Do not rewrite every markdown file for style-only reasons.

## User Stories or Primary User Outcomes

- As a maintainer, I can update a workflow rule in its owner file and know where summaries are allowed.
- As an implementation agent, I can read a high-level skill and understand which lower-level contracts it composes without receiving conflicting detail.
- As a reviewer, I can run one validation command and catch stale README skill rows, modifier mismatch, missing owner paths, and known duplicate contract details.

## Functional Requirements

- `FR-001`: The repo must define a clear contract-ownership convention for public skills, shared references, and intentional mirrors.
- `FR-002`: The plan-and-execute orchestration surface must remain public and usable while delegating detailed planning, refinement, execution, review, and finalization behavior to owned references.
- `FR-003`: The task-file contract must own path, activation, artifact naming, mode entry, and temporary/archive file contracts without acting as a second full copy of child workflow rules.
- `FR-004`: The README skill invocation table must remain consistent with public skill front matter and supported modifiers.
- `FR-005`: CI must run a validator that catches contract metadata drift and the first known stale-mirror patterns.
- `FR-006`: The change must preserve existing installer behavior and current public Prime Directive workflow semantics.

## Acceptance Criteria

- `FR-001`: A new shared reference identifies owner files, consumers, and mirror policy for the major contracts.
- `FR-002`: `skills/plan-and-execute/SKILL.md` is shorter and references owned contracts for detailed behavior instead of duplicating them.
- `FR-003`: `skills/shared/references/execution/task-file-contract.md` keeps canonical activation/path/mode rules and routes detailed child behavior to the owning skill or shared reference.
- `FR-004`: The validator fails if README skill names or public modifier lists drift from `skills/*/SKILL.md`.
- `FR-005`: `.github/workflows/validate.yml` runs the new validator.
- `FR-006`: Existing installer validation still passes, and the new validator passes locally.

## Product Rules / UX Rules / Content Rules

- Public workflow names and modifier names are part of the product surface and must remain stable.
- Higher-level docs may include tiny summaries for orientation, but detailed behavior must live in the owner file.
- Cross-references should use repo-relative `skills/...` paths.
- Mirrors should be deliberate and small enough that they do not become alternate sources of truth.

## Constraints and Defaults

- Default to one cohesive PR because this repo is tiny.
- Execution must not silently mix unrelated branch or PR scope. Before implementation edits, the workflow must record the current branch, upstream, and open PR state. If an open PR exists and its title/scope does not match `contract-ownership-refactor`, implementation must stop for user direction unless explicit reuse approval is already recorded.
- Keep the validator lightweight and stdlib-based so it can run in GitHub Actions without dependency setup.
- Prefer explicit ownership tables and deterministic checks over another agent-run audit workflow.
- Defer exact helper names and script internals to execution after inspecting existing script style.

## Success Metrics / Guardrails

- Validation command exits cleanly in a fresh checkout.
- Installer idempotence validation continues to pass.
- Review finds no stale duplicated challenger-lane, plan-and-execute, or finalization contract text.
- Skill docs remain readable after deduplication; references do not force maintainers through unnecessary depth for common edits.
