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

- [x] Implement the validator and focused tests.
- [x] Wire the validator into Deliver and the shared review protocol.
- [x] Validate and install the exact v6 candidate.
- [x] Record the candidate commit.
- [ ] Run the two-scenario comparison only if separately approved.

## Candidate Evidence

- Candidate commit: `733810b`.
- Seven focused validator tests pass, including the exact mutation-plus-output condition that v5 misclassified.
- Contract validation, the frozen Deliver ledger, and `git diff --check` pass.
- A fresh `gpt-5.6-sol` `xhigh` forward-test derived an isolated repair as `targeted`, a persistent-state/output repair as `full`, and their grouped round as `full`; both validator phases passed.
- The local Prime Directive plugin links were reinstalled from the exact candidate checkout.
- The generic system `quick_validate.py` passed using PyYAML 6.0.3 in an isolated temporary virtual environment; the system Python remained unchanged.

## V6 Run Setup

- The user separately approved the full two-scenario rerun on 2026-08-21.
- The official baseline remains the original pre-policy Deliver control `a4116bb`, matching v5 so the unchanged hard gate can measure both test-value and rereview-cost axes.
- One completed Queuectl arm using the failed v5 candidate `3c71231` as an incremental baseline was excluded before any v6 candidate arm, normalization, judge packet, or outcome scoring. It remains diagnostic only.

## V6 Frozen Result

- Final result: `candidate_regression`. The blinded judge preferred the candidate, but the frozen category gate rejected it.
- Correctness was preserved. Both Queuectl arms passed all 7 frozen acceptance checks and 7 of 11 post-hoc diagnostics; both historical holdout arms passed the corrupt-throttle and asynchronous-preflight probes.
- Queuectl baseline: 24 added test functions, 930 added test lines, one full rereview, and 5,139 seconds. Queuectl candidate: 8 added test functions, 388 added test lines, one full rereview, and 2,751 seconds.
- Historical baseline: 79 added test lines, one full rereview, and 1,142 seconds. Historical candidate: no permanent test additions, two full rereviews, and 1,364 seconds. The second candidate round was safety-required after the first rereview found and repaired a leading-zero throttle defect.
- Aggregate baseline: 1,009 added test lines, two full rereviews, and 6,281 seconds. Aggregate candidate: 388 added test lines, three full rereviews, and 4,115 seconds.
- The fresh blinded `gpt-5.6-sol` `xhigh` judge froze `Run A better`; identity reveal mapped Run A to the candidate.
- Candidate field compliance passed. The hard gate improved unjustified permanent decisions from 4 to 0 and unnecessary full classifications from 3 to 1.
- The remaining regression is Queuectl `RF-001`: expected `rereview_scope: targeted`, actual `full`. The deterministic rule correctly repaired v5's `RF-002` under-scoping but overcorrected the separate chronological-selection repair.
- The first historical pre-packet launch from the enclosing workspace sandbox produced an empty trace because nested `sandbox-exec` was denied. It was excluded before any result; both official historical arms were freshly prepared and completed under the evaluator's approved outer Seatbelt boundary.
- Preserved artifacts: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v6/results/`, including all four sealed normalized arms, blind packets, frozen verdict, compliance report, and outcome gate.
- Per the frozen no-tuning rule, do not revise v6 or rerun it inside this comparison. Any narrower RF-001 rule is a separately approved v7 iteration.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v6.md
baseline_ref: a4116bb
candidate_ref: 733810b
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
