See `skills/shared/references/execution/task-management.md` for execution workflow and review guidelines.

# Deep Research Contract Hardening

## Scope Summary

This plan hardens Prime Directive's `--deep-research` contract so agents must prove source quality, research-to-artifact carry-forward, completion, and downstream preservation. It also locks the interaction with `--pro-analysis` and `--refine-plan` so later planning passes cannot silently bypass or weaken research-backed decisions.

Highest-risk implementation concerns:

- Avoiding bloated repeated instructions across multiple skill files.
- Preserving the already-discussed combined modifier order.
- Making audit rules concrete enough for agents without adding new scripts or human approval gates.

## Relevant Files

- `skills/shared/references/planning/deep-research.md` - Primary deep-research contract.
- `skills/plan-work/SKILL.md` - Planning workflow and memo handoff to improve-plan.
- `skills/shared/references/planning/create-tdd.md` - Durable TDD research rationale.
- `skills/shared/references/planning/generate-tasks.md` - Tasks-plan gate and research carry-forward.
- `skills/shared/references/planning/improve-plan.md` - Audit pass for deep-research compliance.
- `skills/plan-and-execute/SKILL.md` - Combined modifier orchestration order.
- `skills/shared/references/execution/task-file-contract.md` - Cross-skill modifier, artifact, and cleanup contracts.
- `skills/plan-refine/SKILL.md` - Refinement guardrails for research-backed decisions.
- `README.md` - Public invocation table and validation commands; update only if modifier surface or recommended checks need clarification.

## Task Ordering Notes

Implement the deep-research core first, then update downstream audit/generation contracts, then update orchestration/refinement interactions. The existing local edits that change combined `--deep-research --pro-analysis` order must be preserved.

## Tasks

- [x] 1.0 Harden the core deep-research memo and evidence contract
  - covers_prd: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-010`
  - covers_tdd: `TDR-001`, `TDR-002`, `TDR-003`, `TDR-004`, `TDR-005`
  - [x] 1.1 Add source-count, source-type, source-family, source-authority, source-conflict, and privacy rules to `deep-research.md`
    - covers_prd: `FR-001`, `FR-002`, `FR-010`
    - covers_tdd: `TDR-001`, `TDR-005`
    - output: `skills/shared/references/planning/deep-research.md`
    - verify: `rg -n "Evidence Ledger|source_id|source_type|source_family|publication_date|last_updated_date|accessed_date|version_or_scope|supported_claims|current_enough_reason|source authority|privacy" skills/shared/references/planning/deep-research.md`
    - done_when: The contract clearly defines which sources count toward the external primary minimum, requires the Evidence Ledger fields named in `FR-001`/`TDR-001`, explains how source conflicts are resolved, and states what private context cannot be sent externally.
  - [x] 1.2 Add draft-linked research questions, finding-to-artifact delta, and completion stamp requirements to `deep-research.md`
    - covers_prd: `FR-003`, `FR-004`, `FR-005`
    - covers_tdd: `TDR-002`, `TDR-003`, `TDR-004`
    - output: `skills/shared/references/planning/deep-research.md`
    - verify: `rg -n "Draft-Linked Research Agenda|Finding-to-Artifact Delta|finding_id|research_question_id|disposition_reason|Deep Research Completion Stamp|evidence_bar_met|source_family_count|follow_up_passes_completed|prd_tdd_sections_changed|task_plan_inputs_created" skills/shared/references/planning/deep-research.md`
    - done_when: The memo cannot be considered complete without draft-linked questions, artifact deltas containing the fields named in `FR-004`/`TDR-003`, and an explicit completion stamp containing the fields named in `FR-005`/`TDR-004`.

- [x] 2.0 Carry research evidence through downstream planning contracts
  - covers_prd: `FR-006`, `FR-007`
  - covers_tdd: `TDR-006`, `TDR-007`, `TDR-008`, `TDR-009`
  - [x] 2.1 Update `plan-work` and task-file cleanup rules so the research memo remains available through planning audits
    - covers_prd: `FR-006`
    - covers_tdd: `TDR-006`
    - output: `skills/plan-work/SKILL.md`, `skills/shared/references/execution/task-file-contract.md`
    - verify: `rg -n "research memo.*improve-plan|until.*improve-plan|until.*plan-refine" skills/plan-work/SKILL.md skills/shared/references/execution/task-file-contract.md`
    - done_when: `improve-plan` receives the memo whenever deep research was used, and cleanup happens only after required planning audits.
  - [x] 2.2 Update TDD, task generation, and improve-plan contracts to audit and preserve research-backed decisions
    - covers_prd: `FR-007`
    - covers_tdd: `TDR-007`, `TDR-008`, `TDR-009`
    - output: `skills/shared/references/planning/create-tdd.md`, `skills/shared/references/planning/generate-tasks.md`, `skills/shared/references/planning/improve-plan.md`
    - verify: `rg -n "research-backed rationale|completion stamp|evidence_bar_met: no|Finding-to-Artifact Delta|Evidence Ledger|adopted.*finding" skills/shared/references/planning/create-tdd.md skills/shared/references/planning/generate-tasks.md skills/shared/references/planning/improve-plan.md`
    - done_when: Final TDD retains compact research rationale, task generation checks completion/carry-forward and stops on `evidence_bar_met: no`, and improve-plan audits the structured memo instead of improving around a failed stamp.

- [x] 3.0 Lock combined modifier and refinement guardrails
  - covers_prd: `FR-008`, `FR-009`
  - covers_tdd: `TDR-010`, `TDR-011`, `TDR-012`
  - [x] 3.1 Update `plan-and-execute` and task-file contract for explicit modifier order and Pro/research reconciliation
    - covers_prd: `FR-008`
    - covers_tdd: `TDR-010`, `TDR-012`
    - output: `skills/plan-and-execute/SKILL.md`, `skills/shared/references/execution/task-file-contract.md`
    - verify: `rg -n "deep research first|Pro.*does not count|Pro-suggested|independently.*verified|Evidence Ledger|reconciliation|primary evidence" skills/plan-and-execute/SKILL.md skills/shared/references/execution/task-file-contract.md`
    - done_when: Combined modifiers are ordered as deep research, Pro analysis, tasks-plan, refine-plan, execution; Pro cannot replace primary evidence; Pro-suggested sources influence source-backed claims only after independent verification and Evidence Ledger recording; conflicts with research or repo facts require reconciliation.
  - [x] 3.2 Update `plan-refine` and task-file contract so refinement cannot silently weaken research-backed decisions
    - covers_prd: `FR-009`
    - covers_tdd: `TDR-011`
    - output: `skills/plan-refine/SKILL.md`, `skills/shared/references/execution/task-file-contract.md`
    - verify: `rg -n "research-backed|research memo|durable research digest|superseded|evidence_bar_met: no|final research-carry-forward" skills/plan-refine/SKILL.md skills/shared/references/execution/task-file-contract.md`
    - done_when: Refinement reads the memo or TDD digest, stops on `evidence_bar_met: no`, and records any superseding/removal of research-backed obligations.

- [ ] 4.0 Validate and review the skill-contract change
  - covers_prd: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `FR-007`, `FR-008`, `FR-009`, `FR-010`
  - covers_tdd: `TDR-001`, `TDR-002`, `TDR-003`, `TDR-004`, `TDR-005`, `TDR-006`, `TDR-007`, `TDR-008`, `TDR-009`, `TDR-010`, `TDR-011`, `TDR-012`
  - [ ] 4.1 Run focused text checks and installer smoke checks
    - covers_prd: `AC-008`, `AC-009`
    - covers_tdd: `TDR-012`
    - output: validation evidence
    - verify: `git diff --check && python3 scripts/alfred-skill-router.py --format list && HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh && HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`
    - done_when: Checks pass or any failures are documented with concrete cause.
  - [ ] 4.2 Run final full-branch review and archive planning artifacts
    - covers_prd: `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-006`, `AC-007`, `AC-008`, `AC-009`
    - covers_tdd: `TDR-001`, `TDR-002`, `TDR-003`, `TDR-004`, `TDR-005`, `TDR-006`, `TDR-007`, `TDR-008`, `TDR-009`, `TDR-010`, `TDR-011`, `TDR-012`
    - output: `tasks/archive/2026-04-21-deep-research-contract-hardening/`
    - verify: final review log plus `find tasks/archive/2026-04-21-deep-research-contract-hardening -maxdepth 1 -type f | sort && test ! -e tasks/prd-deep-research-contract-hardening.md && test ! -e tasks/tdd-deep-research-contract-hardening.md && test ! -e tasks/tasks-plan-deep-research-contract-hardening.md`
    - done_when: Review finds no unresolved blocker/material issues, all task checkboxes are complete, PRD/TDD/tasks-plan are archived, and no duplicate active planning set remains under `tasks/`.
