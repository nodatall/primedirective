# Deliver Skill Review: Cross-Run Isolation V11

## Authorized Change

- Preserve exact Deliver baseline `a4116bb` and exact candidate `8a489bc`; do not change candidate-owned skill, shared review, rereview validator, test, or contract-validator surfaces.
- Preserve both scenarios, fixtures, findings, approvals, stop boundaries, hidden checks, diagnostic probes, outcome ledger, judge rubric, timeout policy, cost gates, and Sol/xhigh routing.
- Repair the evaluator's sole outer execution boundary so an arm can access its own stage but cannot read or write any other `/private/tmp` path, including older `deliver-eval-*` run roots.
- Add an evaluator-owned external-temp sentinel outside every arm root to the mandatory first-tool gate and the actual Seatbelt integration probe. The harness must create and verify a canonical regular file with fixed bytes and digest before a runner starts, reject a missing file, symlink, or changed digest, and re-verify unchanged bytes after the runner exits. Retain it through final merge rereview so the frozen chain remains replayable, then delete the exact sentinel/runtime only during terminal closeout after the preserved evidence and merge-ready result are committed.
- Keep the current home, volume, sibling, environment, authentication-copy, stream-capture, and process-group protections. The host proof must also cover `/tmp` aliasing, relative traversal, and a symlink inside the allowed stage that targets the denied external sentinel.
- Update only this exact evaluator allowlist: `evals/deliver/harness.py`, `evals/deliver/tests/test_harness.py`, `evals/deliver/suite.md`, `evals/deliver/evaluator/output-freeze-schema.json`, `evals/deliver/evaluator/behavior-schema.json`, `evals/deliver/evaluator/terminal-seal-schema.json`, `evals/deliver/evaluator/candidate-compliance-schema.json`, and one new consolidated `evals/deliver/evaluator/comparison-artifacts-schema.json`. No fixture, scenario, rubric, ledger, prompt, approval, stop-boundary, timeout, cost-gate, candidate-owned file, validator, or unrelated evaluator surface may change.

## Proof Gates Before Official Arms

- Empirically prove on the host that a broad `/private/tmp` deny plus a narrow current-stage allow permits current-arm reads/writes while denying external-sentinel reads and writes through `/private/tmp`, the `/tmp` alias, relative traversal, and an allowed-stage symlink escape. The test must first prove the sentinel is a regular file with its expected digest and afterward prove it still exists unchanged, so absence cannot produce a false pass.
- Run the complete harness suite with the actual nested Seatbelt test outside the enclosing workspace sandbox, and require every current-stage, external-sentinel, alias, traversal, symlink-escape, home, volume, sibling, authentication, and inherited-environment assertion to execute rather than skip.
- Run the frozen ledger check, skill-contract validator, Deliver validator tests, quick skill validation, and diff checks.
- Before the first arm starts, require a clean evaluator allowlist, zero diff under every candidate-owned path, exact extracted package SHA-256 manifests for baseline `a4116bb` and candidate `8a489bc`, and a committed evaluator identity consisting of its commit, `evals/deliver` Git tree, and canonical file-manifest SHA-256. Recompute the current evaluator tree and canonical evaluator-file manifest at every preflight/finalization/normalization/gate boundary and require those bytes to equal the frozen identity; after the official comparison, result-only commits outside `evals/deliver` may advance repository `HEAD` without changing that identity. Carry it through runner preflight, phase metadata, output freeze, terminal seal, normalized output, blind packet, frozen judge record, identity reveal, candidate-compliance result, outcome gate, and final verdict. Each downstream artifact must bind the SHA-256 of every exact upstream input it consumes plus the same frozen evaluator/comparison identity. All official commands must execute with that one immutable evaluator tree.
- Before preflight, create one frozen comparison manifest with a unique comparison ID, evaluator identity, exact package manifests, runtime root, exact four-arm order, and attempt policy. Define comparison identity as the SHA-256 of that manifest's canonical JSON bytes; recompute that digest rather than trusting the embedded ID at every decisive boundary. Maintain evaluator-owned durable attempt state outside every arm stage. The harness must reject an out-of-order arm start, any second start after a valid terminal seal, any second seal submission, and any normalization, judge, reveal, compliance, gate, or final-verdict input that does not belong to that exact manifest digest. Record the only permitted restart—an externally interrupted, unsealed arm with byte-identical inputs—in the attempt state before it starts again.
- Seal registration is one atomic state transition under an exclusive evaluator-owned lock: exactly one active attempt may move from unsealed to sealed with exactly one terminal-seal digest. A duplicate or concurrent seal submission must fail without changing the first binding; cover both cases with focused harness tests.
- The evaluator closes to edits when arm 1 starts. No official arm may be rerun after a valid terminal seal.

## Fresh Comparison

- Precommit this exact four-arm order and run it sequentially from the unchanged contract packages and newly frozen evaluator: (1) `retry-failed` baseline, (2) `retry-failed` candidate, (3) `preflight-remediation-holdout` baseline, and (4) `preflight-remediation-holdout` candidate.
- Obtain one fresh blinded `gpt-5.6-sol` `xhigh` judge verdict before identity reveal.
- After reveal, require candidate compliance, zero category regressions, strict improvement on both frozen cost axes, preserved material correctness, and a blinded candidate-better verdict.
- Preserve all v10 evidence as the superseded comparison that exposed the isolation defect; do not reuse its normalized outputs in v11.

## Failure Transitions

- A harness/evidence defect discovered before arm 1 is repaired, validated, and rereviewed in this authorized v11 evaluator slice.
- Once arm 1 starts, any evaluator defect, baseline-caused terminal failure, ambiguous failure layer, incomparable input/evidence state, or material correctness ambiguity makes v11 `inconclusive/uncomparable_runs` and requires a separately planned and frozen v12. Do not tune or rerun sealed v11 results.
- Apply this exact transition matrix after the highest-precedence applicable condition is known:

| Condition | `verdict` | `stop_reason` | Merge ready | Restart authority and next action |
| --- | --- | --- | --- | --- |
| Evaluator defect, baseline-caused terminal failure, ambiguous layer, or incomparable evidence | `inconclusive` | `uncomparable_runs` | no | no v11 rerun; separately plan and freeze v12 |
| Candidate-caused unscorable arm, candidate hard-gate failure, or blinded regression | `candidate_regression` | `candidate_regression` | no | no v11 rerun; separately freeze a candidate revision |
| Scenarios do not expose the changed contract | `inconclusive` | `inconclusive_scenario` | no | replace or extend scenarios only in a separately authorized frozen version |
| Valid blind verdict is materially neutral and all hard gates pass | `candidate_neutral` | `candidate_neutral` | no | preserve evidence; require a separately frozen change for another attempt |
| Blind verdict is candidate-better; compliance, correctness, category, and both strict cost gates pass | `candidate_better` | `clean_benefit` | yes, subject to final merge rereview | freeze evidence and continue only to merge rereview |
| External interruption before an arm seal or judge freeze | `inconclusive` until resumed | `external_interruption` | no | one byte-identical restart recorded by the comparison attempt state; then re-enter the matrix |

- Apply precedence in this order: evaluator or comparability defect; candidate-caused unscorable/regression; candidate-not-exposed; neutral; clean benefit.
- Only an external interruption may restart an unsealed arm or an unfrozen judge with byte-identical inputs. A sealed arm may resume at normalization without rerunning. A frozen blinded verdict may resume at identity reveal and gates without rerunning the judge. All other restarts require the next separately frozen version.

## Status

- [x] Complete a fresh adversarial plan review.
- [x] Implement and validate the evaluator isolation fix without changing candidate `8a489bc`.
- [x] Complete a fresh adversarial implementation review and freeze the exact evaluator.
- [ ] Run four fresh sealed official arms and a fresh blind judge.
- [ ] Apply candidate compliance and the unchanged hard gate.
- [ ] Preserve artifacts and record the terminal v11 verdict.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v11.md
baseline_ref: a4116bb
candidate_ref: 8a489bc
evaluator_ref: 73fa8de6b3d10c3c8111debcaf525dd2cfcc87aa
evaluator_tree: 0971260022313abbd0a1111bf9f20fa7c7a08113
evaluator_manifest_sha256: c15d17e58533ad2c9bbb88109bcca75e5679230c738d6bb251c1a456c0270fec
scenario: evals/deliver/suite.md
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: no
ready_for_merge_review: no
stop_reason: official_comparison_pending
