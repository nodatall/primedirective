# Plan Refine Log: deep-research-contract-hardening

effective_max_rounds: 8

## Round 1

Findings:

- `DRCH-R1-001` material cross-artifact: exact Evidence Ledger and completion-stamp field sets were not locked tightly enough.
  - fix: Updated `FR-001`, `FR-005`, `TDR-001`, `TDR-004`, and task 1.1/1.2 verification and done conditions to name the required audit fields.
- `DRCH-R1-002` material cross-artifact: Pro-suggested source handling was under-specified.
  - fix: Updated `FR-008`, `TDR-010`, and task 3.1 to require independent verification and Evidence Ledger recording before Pro-suggested sources can influence source-backed claims.
- `DRCH-R1-003` material TDD: CI coverage incorrectly claimed the GitHub workflow runs the Claude installer.
  - fix: Corrected the current technical diagnosis to state CI validates the Alfred router and Codex installer idempotence only; Claude installer remains a local smoke check.
- `DRCH-R1-004` minor tasks-plan: archive verification did not confirm active planning files were removed.
  - fix: Added archive verification that checks the files moved into archive and no active duplicate planning set remains.

Stop decision: fixes applied; run one more fresh reviewer round to confirm no remaining blocker or material findings.

## Round 2

Findings:

- `DRCH-R2-001` material cross-artifact: Finding-to-Artifact Delta fields were not locked as explicitly as Evidence Ledger and Completion Stamp fields.
  - fix: Updated `FR-004`, `TDR-003`, and task 1.2 verification/done conditions to require `finding_id`, `research_question_id`, `bucket`, `disposition`, `recommendation`, `recommendation_level`, `support_type`, `source_ids`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `disposition_reason`.
- `DRCH-R2-002` material cross-artifact: downstream contracts did not explicitly require hard stops on `evidence_bar_met: no`.
  - fix: Updated `AC-004`, `AC-005`, `AC-007`, `TDR-008`, `TDR-009`, `TDR-011`, and task 2.2/3.2 verification and done conditions to require downstream handling of `evidence_bar_met: no`.

Stop decision: fixes applied; run one more fresh reviewer round to confirm no remaining blocker or material findings.
