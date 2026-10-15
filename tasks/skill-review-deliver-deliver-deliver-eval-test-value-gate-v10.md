# Deliver Skill Review: Exact Categories And First-Pass Verification V10

## Approved Change

- Preserve the v9 attestation gate, dual-purpose ordinary review, pathological-trigger probe default, credible-harm escape, no-invented-harness rule, in-place validator rule, schema v3, and every existing full-review trigger.
- Make the three v9 hard-gate decisions explicit without scenario-specific identifiers in the skill contract:
  - keep one standalone permanent regression for a uniquely uncovered material semantic invariant when it does not share its boundary, expected result, and failure mechanism with a coherent table; chronology that determines irreversible selection is one example, not a keyword rule;
  - derive full scope from the defect boundary changed or protected by a repair, including a pre-repair fallible output/diagnostic failure after irreversible mutation even when the repair moves validation before mutation;
  - keep an isolated restoration targeted when no other full trigger or new material finding applies.
- Add compact first-pass checks for parser guards versus downstream consumer grammar and for approved cross-process lifecycle repairs, so predictable adjacent defects are found before the first full review rather than through repeated review rounds. A synchronous caller must not return while protected work or its live owner/lock remains active, even after an intermediate readiness signal; verification includes concurrent waiters and failed/stale owners.
- Keep disposable historical checks probe-only and do not add a permanent harness or copy the Deliver validator into target repositories.

## Frozen Evaluation Contract

- Keep the evaluator, outcome ledger, scenarios, fixtures, prompts, approvals, stop boundaries, hidden checks, diagnostic probes, judge rubric, harness, timeout policy, cost gates, original baseline `a4116bb`, and Sol/xhigh routing unchanged from v9.
- Keep `beb346a:evals/deliver` tree `d7da128ff8aef384e49cdfc8ccd593129d82b8e4` and require zero diff under `evals/deliver/**` before official arms.
- Queuectl expected categories remain RF-001 `permanent/targeted`, RF-002 `table_case/full`, RF-003 `probe_only/targeted`, and RF-004 `no_test/null`.
- Historical expected categories remain PF-001 `probe_only/targeted` and PF-002 `probe_only/full`.
- Use fresh `gpt-5.6-sol` `xhigh` agents for plan review, implementation/forward review, all four official arms, and the blinded judge.
- Passing still requires preserved material correctness, strict improvement on both frozen cost axes, candidate compliance, a blinded candidate-better verdict, and zero candidate category regressions.

## Failure Transitions

Use the v9 precedence and restart limits with `current_version=v10` and `next_candidate_version=v11`:

- Invalid comparison from evaluator/harness defect, baseline-caused terminal failure, or evidence-layer ambiguity: `inconclusive` / `uncomparable_runs`; stop for separate authorization.
- Otherwise candidate-caused unscorable output, blinded regression, or any hard-gate failure: `candidate_regression`; preserve and commit v10, then change candidate-owned surfaces only in v11.
- Otherwise neutral: `candidate_neutral`; not merge-ready and only a separately frozen candidate-owned v11 may continue.
- Otherwise candidate-not-exposed: `inconclusive_scenario`; preserve v10, revise candidate-only when evidence supports it or stop separately.
- Only an externally interrupted unsealed arm or unfrozen judge stage may restart with unchanged inputs. Preserve every terminal seal and frozen verdict.
- A full pass maps to `candidate_better` / `clean_benefit` and continues to exact-candidate merge review.

## Status

- [x] Complete a fresh adversarial v10 plan review; the revised mechanism-based plan returned clean.
- [x] Implement only candidate-owned contract wording and proportional validator tests.
- [x] Validate and independently forward-test all six frozen action outcomes plus RF-004 null scope, same-mechanism table and unchanged-reporting targeted negative controls, parser-consumer grammar, concurrent waiters, failed/stale owners, and post-readiness protected-work completion.
- [x] Complete fresh adversarial implementation review, install, commit, and record the exact candidate.
- [x] Run four sealed official arms and a fresh blind judge.
- [x] Apply candidate compliance and the unchanged hard gate.
- [x] Preserve artifacts and record the terminal v10 verdict without in-run tuning.

## Terminal Result

- Verdict: `candidate_better` / `clean_benefit`.
- Blinded judge: Run B better; the frozen operator reveal mapped Run B to the candidate.
- Material correctness: both arms passed the frozen acceptance checks; the judge preferred the candidate's additional supported output-after-persistence and cross-process completion protection.
- Test-value gate: unjustified permanent decisions improved from 2 to 0.
- Rereview-scope gate: unnecessary full rereviews improved from 3 to 0.
- Candidate category regressions: none across all six frozen findings.
- Candidate compliance: passed with no violations.
- Aggregate measured execution: baseline 19 test functions, 531 test lines, 3 full rounds, 2,777 seconds; candidate 14 test functions, 615 test lines, 4 full rounds, 5,718 seconds. The qualitative judge accepted the higher time and line cost because the candidate closed material adjacent correctness boundaries and removed unjustified permanent/scope decisions.
- Preserved evidence: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v10/results/` and `/private/tmp/deliver-eval-8a489bc-v10-official/`.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v10.md
baseline_ref: a4116bb
candidate_ref: 8a489bc
scenario: evals/deliver/suite.md
baseline_run_complete: yes
candidate_run_complete: yes
comparable_inputs: yes
judge_run_complete: yes
judge_blinded: yes
verdict: candidate_better
artifact_evidence_preserved: yes
ready_for_merge_review: yes
stop_reason: clean_benefit
