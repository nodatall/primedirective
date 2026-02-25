---
description:
globs:
alwaysApply: false
---
# Rule: Generating a Product Requirements Document (PRD)

## Goal

Generate a product-only PRD that clearly defines **what** to build and **why**, after Socratic planning decisions are locked.

The PRD must be decision-complete for product intent, but must not contain deep implementation design.

## Process

1. **Receive Feature Reference:** The user provides a feature name and planning context.
2. **Validate Socratic Prerequisites (Required):** Confirm `tasks/socratic-<feature>.md` and `tasks/decision-log-<feature>.md` exist and reflect accepted readiness.
3. **Gate Check (Required):** Do not generate PRD unless:
   - unresolved high-impact unknowns are zero,
   - core behavior decisions are explicit,
   - user accepted the plain-language summary + checklist.
4. **Ask Product Clarifications Only:** If product intent is still ambiguous, ask focused clarifying questions about problem/scope/outcomes. Do not drift into implementation design.
5. **Generate PRD:** Produce `tasks/prd-<feature>.md` with required sections and stable requirement IDs (`FR-*`).
6. **Handoff Integrity Check (Required):** Ensure every `FR-*` has mapped acceptance criteria and the `Handoff to TDD` section is complete.
7. **Save PRD:** Write the finalized document to `/tasks/prd-<feature>.md`.

## Clarifying Questions (Examples)

Use only as needed to close product-level ambiguity:

- Problem/Goal: exact problem and user outcome.
- Target User: primary persona(s).
- Core Functionality: key user-visible behaviors.
- Scope/Boundaries: explicit non-goals.
- Success Criteria: measurable outcomes.
- Constraints: policy, compliance, operational limits.

## PRD Structure

The PRD must include:

1. **Overview**
2. **Goals**
3. **User Stories**
4. **Functional Requirements** with stable IDs (`FR-*`)
5. **Acceptance Criteria** mapped to every `FR-*`
6. **Non-Goals**
7. **Constraints**
8. **Success Metrics**
9. **Open Questions** (if any)
10. **Handoff to TDD** (required):
    - Technical decisions needed
    - Operational requirements
    - Integration boundaries

## Target Audience

Assume the primary reader is a junior developer and a product approver. Keep language explicit, low-jargon, and unambiguous.

The PRD should be complete on product intent while intentionally avoiding deep technical implementation details.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `prd-<feature>.md`

## Final instructions

1. Do NOT start implementing the PRD
2. Do NOT generate a PRD if Socratic readiness gates are unmet
3. Ask only the minimum product clarifications needed to remove ambiguity
4. Keep PRD product-only; move implementation depth to TDD
5. After PRD approval, generate `tdd-<feature>.md` using `rules/create-tdd.md`
6. After task generation is completed for this PRD, run `rules/improve-plan.md` to refine the PRD + task plan before implementation
7. Hard stop gate: completion of PRD/TDD/tasks planning does not authorize implementation. Start build only when user provides `begin task <task-id> in <prd-key>` or `begin one-shot in <prd-id>`.
