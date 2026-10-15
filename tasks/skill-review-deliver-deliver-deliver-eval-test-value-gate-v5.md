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
- [x] Run both unchanged scenarios with fresh baseline and candidate arms.
- [x] Freeze and normalize all four arms.
- [x] Obtain a fresh blinded verdict and reveal identities only afterward.
- [x] Apply candidate compliance and the v5 outcome ledger.
- [x] Stop without tuning unless the combined verdict is `candidate_better` and all hard gates pass.

## Results

- All four fresh arms completed, sealed, and normalized under the same `gpt-5.6-sol` `xhigh` runner and 5,400-second per-arm budget.
- Both Queuectl arms passed 7/7 frozen hidden checks and the supplied depth probe; both passed 7/11 post-hoc diagnostics. Both historical holdout arms passed both frozen probes.
- The candidate reduced Queuectl permanent coverage from 24 added test functions and 721 added lines to 6 functions and 225 lines. Across both scenarios, candidate wall time was 2,776 seconds versus 3,376 seconds for baseline.
- Candidate compliance passed. The outcome gate recorded strict improvement on both cost axes: unjustified permanent decisions fell from 2 to 0 and unnecessary full rereviews fell from 3 to 0.
- The hard outcome gate nevertheless failed because Queuectl RF-002 was rereviewed as `targeted` when the frozen mutation/output boundary required `full`.
- The fresh blinded judge selected Run B. Identity reveal mapped Run B to baseline, so the official verdict is `candidate_regression`.
- Evidence is preserved under `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v5/results/`, including all normalized arms, freezes, seals, blinded packets and verdict, compliance result, and outcome gate.

## Limitations

- The result covers two scenarios, not general Deliver behavior.
- Both Queuectl arms retained four post-hoc diagnostic exposures; these were diagnostic rather than frozen acceptance checks.
- V5 solved the historical cross-process rereview case and the test-bloat objective, but its wording or enforcement did not make the Queuectl mutation/output full-review trigger reliable enough.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v5.md
baseline_ref: a4116bb
candidate_ref: 3c71231
scenario: evals/deliver/suite.md
baseline_run_complete: yes
candidate_run_complete: yes
comparable_inputs: yes
judge_run_complete: yes
judge_blinded: yes
verdict: candidate_regression
artifact_evidence_preserved: yes
ready_for_merge_review: no
stop_reason: candidate_regression
