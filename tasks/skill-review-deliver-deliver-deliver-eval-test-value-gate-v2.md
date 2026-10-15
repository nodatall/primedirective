# Deliver Skill Review: Test-Value Gate v2

Invocation: `$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=a4116bb candidate=83cf702 --preserve-review-artifacts`

- Skill: `deliver`
- Baseline contract: `a4116bb`
- Candidate contract: `83cf702`
- Frozen harness: `50fa61e`
- Scenario suite: `evals/deliver/suite.md`
- Runner and judge: `gpt-5.6-sol`, `xhigh`
- Arm budget: 90 cumulative active minutes across pre-packet and remediation
- Inactivity timeout: 15 minutes without a structurally valid Codex JSONL event
- Preserved artifacts: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v2/results/inconclusive-holdout-leak/`
- Runtime root: `/private/tmp/deliver-eval-50fa61e-v2/`
- Verdict: `inconclusive`
- Merge readiness: blocked

The 900-second and 1,800-second v1 attempts are invalid diagnostics and are excluded from every v2 score. Both v2 arms receive the same clean fixture, contract-specific package, model, reasoning level, tools, sandbox, cumulative budget, inactivity policy, and staged review packet. Any frozen-ledger failure, material correctness loss, incomplete arm, or verdict other than `candidate_better` stops this version without tuning or another retry.

## Stop Evidence

The versioned timeout repair worked. Both Queuectl arms completed both phases with authoritative terminal traces:

- Baseline: 490.060 seconds pre-packet plus 1,303.417 seconds remediation; 1,793.477 seconds total.
- Candidate: 2,119.468 seconds pre-packet plus 720.803 seconds remediation; 2,840.271 seconds total.

The historical holdout then failed its frozen two-stage contract. Its pre-packet prompt said to inspect the pinned starting state without anticipating findings or editing before the fixed review packet was staged. However, the runner-visible `scenario/acceptance-contract.md` already disclosed both exact defect mechanisms and expected repairs. The baseline implemented and committed both repairs during `scenario_stage: pre_packet`, changing both pinned scripts by 20 insertions and 7 deletions before packet staging. Its trace explicitly claimed it was resuming remediation and inspecting a staged packet that did not yet exist.

That mutation makes the holdout uncomparable: its fixed packet no longer targets the frozen starting state, and the candidate could not receive an equivalent undisclosed remediation decision. The candidate holdout was not started. Queuectl hidden checks, arm finalization, normalization, the outcome ledger, candidate compliance, and the blinded judge were not run after this hard stop. No v2 scenario, harness, contract, or ledger tuning was performed after observing the failure.

A new user-approved versioned iteration must remove the holdout defect details from every pre-packet runner-visible file, add a fail-closed no-source-mutation gate for that stage, and rerun both scenarios from clean snapshots. The completed v2 Queuectl arms and invalid holdout baseline are diagnostic evidence only and must not be reused for scoring.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v2.md
baseline_ref: a4116bb
candidate_ref: 83cf702
harness_ref: 50fa61e
scenario: evals/deliver/suite.md
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: yes
ready_for_merge_review: no
stop_reason: uncomparable_runs
