# Deliver Skill Review: Test-Value Gate V5

## Comparison

- Skill: `deliver`
- Baseline: `a4116bb`
- Candidate: `3c71231`
- Scenarios: Queuectl Retry Failed Jobs and historical preflight remediation holdout
- Runner, reviewer, and judge: `gpt-5.6-sol`, `xhigh`
- Budget: 5,400 cumulative active seconds per arm
- Scratch: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v5/`

## V4 Evidence Driving This Iteration

- The candidate substantially reduced permanent-test size and review cost, but its targeted Queuectl rereview missed mutation before an output-encoding failure.
- Its targeted historical rereview missed cross-process lock and completion races that the baseline full review found and repaired.
- Both historical arms used one-run probes because the exact two-script fixture has no tracked test harness, so requiring table or permanent cases there was not a feasible evaluator expectation.

## Candidate Hypothesis

Keep the early Deliver test-value decision. Require a full rereview when a repair changes cross-process coordination, lifecycle or completion semantics, or the ordering of irreversible mutation relative to user-visible output or diagnostics. Keep isolated repairs targeted. In the evaluator, classify both historical holdout tests as `probe_only`, while retaining PF-002's safety-required full rereview.

## Status

- [x] Implement and validate the smallest v5 contract and evaluator change.
- [x] Freeze the exact candidate/evaluator ref.
- [ ] Run both unchanged scenarios with fresh baseline and candidate arms.
- [ ] Freeze and normalize all four arms.
- [ ] Obtain a fresh blinded verdict and reveal identities only afterward.
- [ ] Apply candidate compliance and the v5 outcome ledger.
- [ ] Stop without tuning unless the combined verdict is `candidate_better` and all hard gates pass.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v5.md
baseline_ref: a4116bb
candidate_ref: 3c71231
scenario: evals/deliver/suite.md
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: yes
ready_for_merge_review: no
stop_reason: missing_judge
