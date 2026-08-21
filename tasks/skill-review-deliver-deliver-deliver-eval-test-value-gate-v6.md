# Deliver Skill Review: Mechanical Rereview Scope Gate V6

## Approved Change

- Keep the v5 test-value policy and rereview triggers.
- Add a bundled deterministic validator for Deliver final-review repair scope records.
- Require every repair action to assess the complete fixed risk-flag set.
- Derive `full` when a full-review flag applies, including the combination of irreversible mutation and user-visible output or diagnostics.
- Derive the executed grouped round from the widest action scope.
- Reject completion when the recorded action or executed round is narrower than the derived scope.

## Frozen Evaluation Contract

- The Queuectl and historical preflight scenarios remain unchanged.
- The frozen outcome ledger remains unchanged, including Queuectl RF-002 `full` and historical PF-002 `full`.
- This implementation step does not authorize another expensive comparison. A v6 run requires a separate explicit request.

## Status

- [ ] Implement the validator and focused tests.
- [ ] Wire the validator into Deliver and the shared review protocol.
- [ ] Validate and install the exact v6 candidate.
- [ ] Record the candidate commit.
- [ ] Run the two-scenario comparison only if separately approved.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v6.md
baseline_ref: 3c71231
candidate_ref: pending
scenario: evals/deliver/suite.md
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: yes
ready_for_merge_review: no
stop_reason: comparison_not_requested
