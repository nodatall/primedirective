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
- [ ] Run both unchanged scenarios through the unchanged evaluator.
- [ ] Freeze and normalize both arms.
- [ ] Obtain a fresh blinded verdict and reveal identities only afterward.
- [ ] Apply the existing stop rule: any verdict other than `candidate_better` ends v4 without tuning.

## Completion Stamp

`in_progress`
