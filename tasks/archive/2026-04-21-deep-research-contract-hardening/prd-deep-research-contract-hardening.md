# Deep Research Contract Hardening PRD

## Plain-Language Summary

Prime Directive already has a `--deep-research` planning mode, but it can still be faked with a pile of links and a memo that does not prove the plan actually improved. This work makes the research pass harder to satisfy cosmetically and easier for later agents to audit.

The improved workflow will require research to show what sources counted, what claims those sources supported, what findings changed the PRD or TDD, and what must carry into task sequencing. It will also make sure later Pro analysis and plan refinement cannot silently override research-backed decisions.

The result should keep the current flow practical: no new default human approval gate, no broad product-discovery sprawl, and no implementation work hidden inside planning. It should strengthen the existing Tech + Delivery research pass without turning it into a generic research template.

## Target User / Audience

Primary users are Codex agents and human operators using Prime Directive planning skills to create implementation-ready PRD, TDD, and task-plan artifacts.

Secondary users are reviewer agents that need to verify whether `--deep-research`, `--pro-analysis`, and `--refine-plan` actually strengthened the plan before execution.

## Problem Statement

The current `--deep-research` contract has strong intent, but too much compliance is prose-based. Agents can satisfy the current checklist by recording source links and memo sections without proving that research was primary-source-backed, version-aware, draft-linked, or carried into PRD/TDD/task sequencing.

## Current-State / Product Diagnosis

`skills/shared/references/planning/deep-research.md` already requires live web research, date anchoring, source freshness notes, primary-source preference, multiple passes, a working memo, PRD/TDD revision before tasks-plan generation, and Tech + Delivery scope.

`skills/plan-work/SKILL.md` runs the research pass after initial PRD/TDD drafts, but currently says `improve-plan.md` receives the research memo only when preserved. That weakens auditability because the normal cleanup path can remove the memo before downstream review has a reliable evidence source.

`skills/plan-and-execute/SKILL.md` and `skills/shared/references/execution/task-file-contract.md` have been locally updated in this thread so combined `--deep-research --pro-analysis` runs deep research first, then Pro analysis before tasks-plan generation. That ordering should remain and be made easier to audit.

`skills/plan-refine/SKILL.md` refines PRD/TDD/tasks-plan after they exist, but it does not yet explicitly protect research-backed decisions from being weakened or removed during refinement.

## Product Goal

Make `--deep-research` a structured, auditable planning upgrade that proves:

- external primary evidence is real and source-typed
- research questions are tied to draft assumptions or artifact sections
- adopted findings are carried into PRD, TDD, and task sequencing
- Pro analysis remains adversarial review, not a substitute for primary evidence
- plan refinement preserves or explicitly supersedes research-backed decisions

## Success Criteria

- Agents can no longer satisfy `--deep-research` with decorative links or generic research prose.
- Research memo requirements emphasize ledgers and completion proof over section volume.
- Downstream `improve-plan`, `generate-tasks`, `plan-and-execute`, and `plan-refine` contracts can audit whether the research pass met the bar.
- Final PRD/TDD/tasks-plan artifacts retain enough durable research rationale after temporary memo cleanup.
- Existing direct-orchestration behavior remains intact: `$plan-and-execute --deep-research` continues without extra approval pauses unless a true blocker appears.

## Explicit Non-Goals

- Do not add new scripts, CLIs, tests, or validators for research memo parsing in this pass.
- Do not introduce broad market research or product-discovery scope as the default.
- Do not add new top-level TDD sections solely for research rationale.
- Do not change public skill names or modifier names.
- Do not change the standalone `$plan-refine` identifier.
- Do not remove existing deep-research evidence requirements unless replacing them with stricter equivalent requirements.

## User Stories or Primary User Outcomes

- As a planning agent, I need the deep-research contract to tell me exactly what evidence and artifact deltas prove the pass is complete.
- As a review agent, I need a compact way to audit source quality, source freshness, findings, and PRD/TDD/task carry-forward.
- As a human operator, I need `--deep-research` to improve implementation quality without creating extra approval gates in direct orchestration mode.
- As an execution agent, I need research-backed decisions to survive plan refinement and remain visible in TDD/task obligations.

## Functional Requirements (`FR-*`)

- `FR-001`: The deep-research memo contract must require an evidence ledger with explicit fields for `source_id`, `source_type`, `source_family`, `url`, `publication_date`, `last_updated_date`, `accessed_date`, `version_or_scope`, `supported_claims`, `counts_toward_external_primary_minimum`, and `current_enough_reason`.
- `FR-002`: The deep-research workflow must define what counts toward the external primary source minimum and what does not.
- `FR-003`: The research process must require draft-linked research questions that can plausibly change PRD, TDD, rollout, verification, or task sequencing.
- `FR-004`: The research memo must require a finding-to-artifact delta ledger with explicit fields for `finding_id`, `research_question_id`, `bucket`, `disposition`, `recommendation`, `recommendation_level`, `support_type`, `source_ids`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `disposition_reason`.
- `FR-005`: The research memo must require a completion stamp with explicit fields for `external_primary_sources_count`, `source_family_count`, `research_questions_answered`, `buckets_reviewed`, `follow_up_passes_completed`, `adopted_findings_count`, `rejected_or_deferred_findings_count`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `evidence_bar_met`.
- `FR-006`: Planning must keep the research memo available through `improve-plan`, and through `plan-refine` when refinement is part of `$plan-and-execute`, before normal cleanup.
- `FR-007`: TDD generation must preserve a compact durable research-backed rationale in existing relevant sections when the temporary memo will be deleted.
- `FR-008`: Combined `--deep-research --pro-analysis` behavior must state that Pro runs after research, does not count as primary evidence, must be reconciled against research and repo facts, and may influence source-backed claims only when any Pro-suggested sources are independently opened, verified, and recorded in the Evidence Ledger.
- `FR-009`: `--refine-plan` behavior must protect research-backed decisions from being silently removed, weakened, or contradicted.
- `FR-010`: Deep research must include version-first stack discovery and a privacy boundary for external searches and prompts.

## Acceptance Criteria

- `AC-001`: `skills/shared/references/planning/deep-research.md` defines evidence ledger, finding-to-artifact delta, completion stamp, source-count rules, source authority/conflict rules, draft-linked question rules, follow-up pass rules, version-first stack discovery, and privacy boundary rules.
- `AC-002`: `skills/plan-work/SKILL.md` requires the research memo to be available to `improve-plan.md` whenever `--deep-research` was used, not only when preserved.
- `AC-003`: `skills/shared/references/planning/create-tdd.md` requires durable research-backed rationale inside existing TDD sections for adopted technical recommendations.
- `AC-004`: `skills/shared/references/planning/generate-tasks.md` verifies the completion stamp, hard-stops when `evidence_bar_met: no`, and maps adopted implementation-impact findings into task sequencing.
- `AC-005`: `skills/shared/references/planning/improve-plan.md` audits the evidence ledger, completion stamp, finding-to-artifact delta, and Pro reconciliation when applicable, and treats `evidence_bar_met: no` as an incomplete planning pass.
- `AC-006`: `skills/plan-and-execute/SKILL.md` and `skills/shared/references/execution/task-file-contract.md` document the combined modifier order and Pro/research reconciliation expectations.
- `AC-007`: `skills/plan-refine/SKILL.md` and `task-file-contract.md` document research carry-forward protection when refinement follows deep research and require refinement to stop when the deep-research completion stamp says `evidence_bar_met: no`.
- `AC-008`: `git diff --check` passes for all touched files.
- `AC-009`: Installer smoke checks still pass for Codex and Claude skill installation flows.

## Product Rules / UX Rules / Content Rules

- Keep instruction text concise and procedural.
- Prefer durable ledgers and completion checks over broad narrative sections.
- Keep the public workflow modifier surface unchanged.
- Do not add human-facing approval prompts unless the existing blocker rules already require them.
- Preserve the existing distinction between standalone `$plan-work` and direct `$plan-and-execute` orchestration.

## Constraints and Defaults

- The repo is a Markdown skill and shell-script repository; validation is mostly text-contract checks plus installer smoke tests.
- The current date for generated artifacts is 2026-04-21 in America/Los_Angeles.
- Existing local edits to `skills/plan-and-execute/SKILL.md` and `skills/shared/references/execution/task-file-contract.md` are related thread work and should be preserved.
- The default branch prefix is `codex/`.

## Success Metrics / Guardrails

- A future agent using `--deep-research` has clear source-count and source-quality rules.
- A future reviewer can audit a research pass without reading all prose linearly.
- A future plan refinement pass cannot silently erase research-backed obligations.
- No unrelated Prime Directive skill behavior changes.
