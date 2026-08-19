# Deliver Skill Review: Test-Value Gate v3

Invocation: `$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=a4116bb candidate=83cf702 --preserve-review-artifacts`

## Run Contract

- Skill: `deliver`
- Baseline contract: `a4116bb`
- Candidate contract: `83cf702`
- Scenario suite: `evals/deliver/suite.md` v3
- Runner and judge: `gpt-5.6-sol`, `xhigh`
- Scratch root: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v3/`
- Runtime root: assigned from the committed v3 evaluator revision before preparation
- Dirty-state rule: the live run starts only after the v3 evaluator is committed and the worktree is clean
- Preserved prior evidence: v1 timeout artifacts and v2 holdout-leak artifacts remain diagnostic only and are excluded from scoring

## V3 Integrity Repair

- The historical holdout exposes only a generic inspection-only starting-state contract before review-packet staging.
- Defect details, acceptance criteria, paused remediation plan, findings, evidence, and probes are staged only after the pre-packet snapshot passes.
- The holdout pre-packet gate requires the exact initial `HEAD`, sole initial branch ref, original Git object closure, initial-only reflog object IDs, no replace/graft/shallow state, and exact pinned source blobs and modes in `HEAD`, index, and worktree.
- Untracked non-source inspection notes are allowed. Pre-packet commits and retained Git history are not.

## Pre-Run Evidence

- Harness tests: 25 passed, including the real outer Seatbelt test outside the enclosing sandbox.
- Skill-contract validator: passed.
- Frozen outcome-ledger validator: passed.
- Whitespace validation: passed.
- Fresh Sol/xhigh integrity review: clean after independently rejecting replace refs, commit-reset, side refs, stash, forged reflogs, loose objects, direct commits, staged and unstaged edits, deletion, and mode drift.

## Run Status

- [x] Baseline Retry Failed Jobs arm completed, finalized, sealed, and normalized.
- [x] Candidate Retry Failed Jobs arm attempted under the same budget and stopped fail-closed at the cumulative timeout.
- [ ] Baseline historical holdout arm not run after the first scenario established a candidate regression.
- [ ] Candidate historical holdout arm not run after the first scenario established a candidate regression.
- [ ] Four-arm finalization and normalization not available because the candidate Retry Failed Jobs arm produced no valid remediation metadata or terminal seal.
- [ ] Frozen outcome gate not run because it requires four normalized outputs.
- [x] Fresh blinded judge completed before identity reveal.
- [ ] Candidate compliance not run because the candidate arm did not finalize.
- [x] Final `candidate_regression` verdict recorded.

## Queuectl Evidence

### Run A

- Identity after reveal: baseline `a4116bb`.
- Completed both phases in 4,101 seconds, then finalized, sealed, and normalized.
- Frozen hidden acceptance: 7/7 passed.
- Post-hoc diagnostics: 7/11 passed. Remaining diagnostic failures covered control-character output, non-finite JSON, overflowing unknown numbers, and sub-microsecond ordering.
- Added 19 test functions and 718 test lines.
- Recorded one full review round, zero targeted rereviews, and actions RF-001 through RF-003 `permanent/full`, RF-004 `no_test/null`.
- Normalized SHA-256: `70e71815471a28c1b250f450e15cbd5362aee80b43ec6412a470ba8153903838`.

### Run B

- Identity after reveal: candidate `83cf702`.
- Pre-packet phase completed in 4,113.586 seconds.
- Public validation was interpreter-dependent: Python 3.14.6 passed 30 tests and failed the permanent depth-1200 assertion because the CLI returned success; runner Python 3.9.6 passed 30 and skipped the integer-limit case.
- Remediation used the remaining 1,286.414 seconds. The cumulative 5,400-second budget expired before a terminal event or valid remediation metadata.
- The harness killed the entire process group, removed the authentication copy, preserved the partial trace, and wrote no output freeze or terminal seal.
- The repository was clean at timeout and contained remediation commits, but the missing terminal lifecycle makes it invalid for normalization and scoring as a completed arm.

## Judge And Stop Decision

- The fresh blinded judge selected Run A as better without knowing contract identity.
- The judge classified the result as a completion/process-cost difference, not evaluator infrastructure ambiguity: Run A completed the entire lifecycle about 12.6 seconds faster than Run B completed its pre-packet phase alone.
- Identity reveal mapped Run A to baseline and Run B to candidate, producing `candidate_regression`.
- The frozen ledger gate, candidate compliance, historical holdout arms, and complete four-output comparison were not run because the first scenario already failed the candidate completion gate.
- Per the pre-registered no-tuning rule, v3 stops here. The budget, suite, candidate contract, and expected outcomes are not changed or rerun inside this iteration.
- Preserved artifacts: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v3/results/candidate-regression-2e0f650/`.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v3.md
baseline_ref: a4116bb
candidate_ref: 83cf702
scenario: evals/deliver/suite.md
baseline_run_complete: yes
candidate_run_complete: no
comparable_inputs: yes
judge_run_complete: yes
judge_blinded: yes
verdict: candidate_regression
artifact_evidence_preserved: yes
ready_for_merge_review: no
stop_reason: candidate_regression
