---
description:
globs:
alwaysApply: false
---
# Rule: Generating a Technical Design Document (TDD)

## Goal

Generate an execution-focused TDD that defines **how** to implement an approved PRD without ambiguity.

PRD is product truth (`what/why`). TDD is execution truth (`how`) and must stay aligned with PRD behavior.

## Process

1. **Receive Feature Reference:** The user provides a feature name with an approved PRD context.
2. **Validate Prerequisites (Required):** Confirm `tasks/prd-<feature>.md` exists and is approved for technical handoff.
3. **Load Planning Context (Required):** Read `tasks/socratic-<feature>.md` and `tasks/decision-log-<feature>.md` when available so technical decisions remain consistent with locked outcomes.
4. **Derive Technical Requirements:** Translate PRD outcomes into stable technical requirements with IDs (`TDR-*`).
5. **Resolve Ambiguity:** If technical execution is unclear, ask targeted implementation clarifying questions (interfaces, dependencies, rollout, recovery). Do not change product behavior without explicit reconciliation.
6. **PRD Alignment Gate (Required):** If proposed technical behavior conflicts with PRD intent, stop and reconcile before finalizing TDD.
7. **Generate TDD:** Produce `tasks/tdd-<feature>.md` using the required structure below.
8. **Command Contract Gate (Required):** Include exact run commands and expected outcomes for build/test/verification flows.
9. **Save TDD:** Write finalized output to `/tasks/tdd-<feature>.md`.

## TDD Structure

The TDD must include:

1. **Overview and Scope Alignment**
2. **Architecture and Component Boundaries**
3. **Data Model and Storage Changes**
4. **Interfaces and Contracts** (API/CLI/events)
5. **Technical Requirements** with stable IDs (`TDR-*`)
6. **Command Contract**
   - exact commands
   - expected outcomes
7. **Failure Modes and Rollback**
8. **Observability and Monitoring**
9. **Test Strategy** (unit/integration/e2e)
10. **Rollout Plan and Operational Runbook**
11. **Open Technical Questions** (if any)

## Required Quality Rules

- Every material execution behavior must map to at least one `TDR-*`.
- Command contract must be executable as written (no placeholder commands).
- Failure detection and rollback paths must be explicit for high-impact paths.
- Do not leave core runtime/dependency behavior as implicit assumptions.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tdd-<feature>.md`

## Final Instructions

1. Do NOT start implementation while creating the TDD
2. Keep TDD aligned to PRD intent; reconcile conflicts before completion
3. Use stable `TDR-*` IDs for technical requirements
4. Ensure command contract and verification paths are concrete enough to run without guessing
5. Generate tasks only after both PRD and TDD are complete
