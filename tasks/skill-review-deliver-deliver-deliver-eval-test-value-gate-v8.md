# Deliver Skill Review: Approved Public Contract Change Gate V8

## Approved Change

- Keep the v7 test-value policy, rereview triggers, deterministic validator, grouped-round enforcement, and ordered-failure protection.
- Replace the ambiguous Boolean risk flag `public_contract` with `changes_approved_public_contract` in schema v3, rejecting v2 and mixed-schema records.
- Add one required `approved_contract_basis` per repair with `effect: none | restore | change | uncertain` and a concise source or evidence citation.
- Require `changes_approved_public_contract` to be true if and only if `effect` is `change`. `uncertain` keeps that Boolean false, must set `isolation_unproven`, and derives full independently. An unsupported restoration fails closed.
- Set `restore` only when evidence identifies a pre-repair approved caller-visible contract and the repair brings implementation back into agreement without revising that contract.
- Set `change` when the repair changes, expands, withdraws, or otherwise revises the approved caller-visible contract itself.
- Preserve every other direct full-review trigger.

## Frozen Evaluation Contract

- Keep both tracked scenarios, fixtures, prompts, approvals, stop boundaries, hidden checks, diagnostic probes, judge rubric, timeout policy, cost gates, and the frozen outcome ledger unchanged.
- Queuectl RF-001 remains `permanent` and `targeted`; RF-002 remains `table_case` and `full`; RF-003 remains `probe_only` and `targeted`.
- Historical PF-001 remains `probe_only` and `targeted`; PF-002 remains `probe_only` and `full`.
- Use the original pre-policy Deliver baseline `a4116bb` so the unchanged gate can still measure strict improvement on both cost axes.
- Use fresh `gpt-5.6-sol` `xhigh` agents for implementation review, all four official arms, and the blinded judge. Do not reuse v7 normalized outcomes.
- A passing result requires preserved material correctness, strict improvement on both frozen cost axes, a passing unchanged outcome ledger and candidate-compliance check, and a blinded `candidate_better` verdict. `candidate_neutral` is not merge-ready for this eval.
- Do not tune v8 or the evaluator after any official arm starts. A comparable scored regression or candidate-caused unscorable result permits only a separately frozen candidate-contract revision with the evaluator, outcome ledger, scenarios, rubric, harness, and cost gates unchanged. An evaluator or harness defect stops for a separate decision. An external runner or environment interruption before the affected arm's valid terminal seal is a recorded non-scoring attempt and may restart the same version only with unchanged frozen inputs. An ambiguous failure stops for a separate decision.

## Failure Transition Table

The same-version arm restart window closes when that arm has a valid evaluator terminal seal. If normalization is interrupted after the seal, resume only from the sealed output. The judge restart window closes when its blinded verdict is frozen; later identity reveal or gate work resumes from that verdict.

Resolve aggregate outcomes in this order: (1) evaluator/harness defect, baseline-caused unscorable output, or evidence-layer ambiguity makes the comparison `inconclusive` and stops for a separate decision; (2) otherwise, a candidate-caused terminal failure or any hard ledger, correctness, compliance, or cost-gate failure maps to `candidate_regression`; (3) otherwise, an external interruption may restart only the affected unsealed arm or unfrozen judge stage with all frozen inputs unchanged; (4) once every arm is sealed and scorable and all programmatic gates pass, map the blinded judge result. A higher-precedence terminal outcome suppresses every lower row, including restart authority.

| Result or failure class | Completion stamp mapping | Same version may restart? | Next action |
| --- | --- | --- | --- |
| Every frozen pass predicate succeeds | `verdict: candidate_better`, `ready_for_merge_review: yes`, `stop_reason: clean_benefit` | No | Continue to exact-candidate merge review. |
| All programmatic gates pass and the comparable blinded result is `candidate_neutral` | `verdict: candidate_neutral`, `ready_for_merge_review: no`, `stop_reason: neutral_no_regression` | No | Preserve and commit v8, then freeze a candidate-only v9 revision if the evidence identifies one. |
| Comparable blinded result is `candidate_regression` even though the programmatic gates pass | `verdict: candidate_regression`, `ready_for_merge_review: no`, `stop_reason: candidate_regression` | No | Preserve and commit v8, then freeze a candidate-only v9 revision. |
| Hard ledger, correctness, compliance, or cost gate fails | `verdict: candidate_regression`, `ready_for_merge_review: no`, `stop_reason: candidate_regression` | No | Preserve and commit v8, then freeze a candidate-only v9 revision. |
| With no higher-precedence invalid-comparison failure, candidate behavior causes an arm to finish without a scorable output or otherwise causes an uncomparable run | `verdict: candidate_regression`, `ready_for_merge_review: no`, `stop_reason: candidate_regression` | No | Preserve and commit v8, then revise only the candidate contract in v9. |
| Evidence attributes a terminal failure or unscorable output to baseline behavior, whether it occurs before or after a seal | `verdict: inconclusive`, `ready_for_merge_review: no`, `stop_reason: uncomparable_runs` | No | This invalid-comparison outcome takes aggregate precedence. Stop for a separate decision; do not treat an attributable baseline timeout as a restartable external interruption or revise the candidate to compensate for it. |
| All programmatic gates pass and the judge is inconclusive because the candidate did not expose the changed behavior | `verdict: inconclusive`, `ready_for_merge_review: no`, `stop_reason: inconclusive_scenario` | No | Preserve and commit v8, then freeze a candidate-only v9 revision if the evidence supports one; otherwise stop for a separate decision. |
| Evaluator or harness defect invalidates comparison | `verdict: inconclusive`, `ready_for_merge_review: no`, `stop_reason: uncomparable_runs` | No | Stop for a separate evaluator decision; do not continue the candidate-only pass loop. |
| With no higher-precedence terminal outcome, an external runner or environment interruption occurs before the affected arm's valid terminal seal, or the judge is interrupted before verdict freeze | Keep the completion stamp incomplete and record the attempt as non-scoring | Yes, only for the affected unsealed arm or unfrozen judge stage and with every frozen input unchanged | Preserve every sealed arm; restart only the interrupted unsealed arm or judge stage, never a sealed arm or frozen verdict. |
| External interruption after all required arms have valid terminal seals but before the blinded verdict freezes | Keep the completion stamp incomplete and record the attempt as non-scoring | No arm rerun; judge may restart only when no verdict froze | Rebuild deterministic normalization from the sealed arm outputs; do not reuse an incomplete or unsealed normalized packet. |
| External interruption after the blinded verdict freezes but before identity reveal or gates | Keep the completion stamp incomplete and record the attempt as non-scoring | No arm or judge rerun | Resume from the frozen blinded verdict and sealed arm evidence. |
| Ambiguous failure whose layer cannot be supported by evidence | `verdict: inconclusive`, `ready_for_merge_review: no`, `stop_reason: uncomparable_runs` | No | Stop for a separate decision. |

Every next-version candidate revision keeps the evaluator, outcome ledger, scenarios, fixtures, prompts, approvals, stop boundaries, hidden checks, diagnostic probes, judge rubric, harness, timeout policy, cost gates, original baseline, and model/reasoning routing frozen.

## Status

- [x] Implement the schema, validator, owner wording, mirrors, and focused tests.
- [x] Validate and forward-test the candidate.
- [x] Run a fresh adversarial implementation review and install the exact candidate.
- [x] Commit and record the exact candidate ref.
- [ ] Run the four-arm frozen comparison and blind judge.
- [ ] Apply candidate compliance and the unchanged hard outcome gate.
- [ ] Preserve artifacts and record the final verdict without in-run tuning.

## Candidate Freeze

- Candidate ref: `beb346a`
- The 13 focused validator tests, full skill-contract validation, quick skill validation, frozen-ledger validation, and `git diff --check` passed.
- The independent forward test produced RF-001/RF-003 `targeted`, a genuine approved-contract change `full`, and an uncertain contract effect `full`; the schema-v3 plan record passed validation.
- The fresh `gpt-5.6-sol` `xhigh` adversarial review found no material issue and confirmed the new cases are table-consolidated and proportional.
- All 25 frozen harness tests passed except the known nested `sandbox-exec` check, which the enclosing sandbox skipped; `evals/deliver/**` is unchanged.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v8.md
baseline_ref: a4116bb
candidate_ref: beb346a
scenario: evals/deliver/suite.md
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: no
ready_for_merge_review: no
stop_reason: missing_candidate
