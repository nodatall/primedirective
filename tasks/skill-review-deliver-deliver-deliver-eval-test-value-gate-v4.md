# Deliver Skill Review: Test-Value Gate V4

## Comparison

- Skill: `deliver`
- Baseline: `a4116bb`
- Candidate: `e62ca5d`
- Evaluator: unchanged suite and harness from `2e0f650`
- Scenarios: Queuectl Retry Failed Jobs and historical preflight remediation holdout
- Runner and judge: `gpt-5.6-sol`, `xhigh`
- Budget: 5,400 cumulative active seconds per arm, unchanged from v3

## V3 Evidence Driving This Iteration

- The candidate used 4,113.586 seconds before remediation and then exhausted the remaining 1,286.414 seconds before it could finish the required full review and finalization.
- The candidate retained an interpreter-dependent depth assertion as permanent coverage.
- Its remediation phase repeated plan refinement before implementation and then entered another full-branch review even though the fixed packet already supplied the approved remediation scope.

## Candidate Hypothesis

Apply the shared test-value decision before any new Deliver test is persisted, so permanent coverage must be supported-path, material, unique, deterministic across supported environments, and economical. During fixed-scope remediation, do not restart plan refinement, and after the one initial full final review, use the existing targeted rereview default unless its escalation rules require a full round.

## Status

- [x] Preserve v3 evidence and diagnose the candidate cost mechanism.
- [x] Implement and validate the smallest candidate contract change.
- [x] Freeze the exact candidate ref.
- [x] Run both unchanged scenarios through the unchanged evaluator.
- [x] Freeze and normalize both arms.
- [x] Obtain a fresh blinded verdict and reveal identities only afterward.
- [x] Apply the existing stop rule: any verdict other than `candidate_better` ends v4 without tuning.

## Frozen Results

### Queuectl Retry Failed Jobs

- Baseline: 7/7 hidden acceptance, 7/11 diagnostic posthoc, 36 added test functions, 980 added test lines, two full review rounds, zero targeted rereviews, 3,173 seconds.
- Candidate: 7/7 hidden acceptance, 7/11 diagnostic posthoc, 9 added test functions, 319 added test lines, zero new full rounds, one targeted rereview, 1,749 seconds.
- The candidate correctly skipped remediation refinement, consolidated related tests, kept the interpreter-dependent depth case as a one-run probe, and used the staged packet as the completed initial full review.
- It still persisted the oversized-integer decoder case in a permanent table, and its targeted review missed an output-encoding atomicity defect that the baseline full review found and repaired.

### Historical Preflight Remediation Holdout

- Baseline: both frozen probes passed, zero added tracked tests, three full review rounds, zero targeted rereviews, 3,044 seconds.
- Candidate: both frozen probes passed, zero added tracked tests, zero full rounds, three targeted rereviews, 2,552 seconds.
- Both runs used one-run probes because the exact two-script holdout has no tracked test harness.
- The candidate kept PF-002 targeted and left pre-existing lock-contention behavior unchanged. The baseline full reviews found and repaired live-lock completion and replacement-lock races, then returned clean after nine probes.

## Judge And Gates

- Blinded packet SHA-256: `4004a71d0be2f9b94cd6ecc1b7e849ddccfcc25fca04f013590a6bc8a9334b71`.
- The fresh blinded judge froze `Run B better` before identity reveal because Run A's lower maintenance cost did not outweigh the two correctness and safety gaps.
- Identity reveal mapped Run A to candidate `e62ca5d` and Run B to baseline `a4116bb`.
- Candidate field compliance passed with no schema violation.
- The cost axes both improved: unjustified permanent decisions fell from 2 to 0, and unnecessary full rereviews fell from 4 to 0.
- The frozen outcome gate still failed four category checks: PF-001 `probe_only` instead of `table_case`; PF-002 `probe_only` instead of `permanent`; PF-002 `targeted` instead of safety-required `full`; RF-003 `table_case` instead of `probe_only`.
- Final verdict: `candidate_regression`. The candidate is not ready for merge review. V4 stops without contract or evaluator tuning.
- Preserved artifacts: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v4/results/candidate-regression-e62ca5d/`.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v4.md
baseline_ref: a4116bb
candidate_ref: e62ca5d
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
