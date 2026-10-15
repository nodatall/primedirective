# Deliver Skill Review: Ordered Mutation And Output Scope Gate V7

## Approved Change

- Keep the v6 test-value policy, rereview triggers, deterministic validator, and grouped-round enforcement.
- Add the explicit Boolean risk flag `fallible_output_after_irreversible_mutation`.
- Set that flag only when the repair changes or protects a path where irreversible state is committed before a user-visible output or diagnostic step that can fail, leaving changed state after an apparent command failure.
- Do not require a full rereview merely because a repair involves both mutation and user-visible reporting when their ordering and failure boundary are unchanged.
- Require the new flag to be consistent with both `irreversible_mutation` and `user_visible_output_or_diagnostics`.

## Frozen Evaluation Contract

- Keep both tracked scenarios, fixtures, prompts, approvals, stop boundaries, hidden checks, diagnostic probes, judge rubric, timeout policy, and the frozen outcome ledger unchanged.
- Queuectl RF-001 remains `permanent` and `targeted`; RF-002 remains `table_case` and `full`.
- Historical PF-001 remains `probe_only` and `targeted`; PF-002 remains `probe_only` and `full`.
- Use the original pre-policy Deliver baseline `a4116bb` so the unchanged gate can still measure strict improvement on both cost axes.
- Use fresh `gpt-5.6-sol` `xhigh` runners for all four official arms. Do not reuse v6 normalized outcomes.
- Do not tune v7 or the evaluator after any official arm starts. Any further contract change requires a separately approved v8 iteration.

## Status

- [x] Implement the schema, validator, owner wording, mirrors, and focused tests.
- [x] Validate and forward-test the candidate.
- [x] Run a fresh adversarial implementation review and install the exact candidate.
- [x] Commit and record the exact candidate ref.
- [x] Run the four-arm frozen comparison and blind judge.
- [x] Apply candidate compliance and the unchanged hard outcome gate.
- [x] Preserve artifacts and record the final verdict without in-run tuning.

## V7 Result

- The first live attempt was interrupted before either arm reached a freeze and left no usable scoring artifact. The official `r2` run restarted the unchanged frozen inputs; only its four sealed arms were scored.
- The blinded judge froze `Run A better`; identity reveal mapped Run A to candidate `3b07ee8`, so the qualitative verdict was `candidate_better`.
- Both runs passed the supplied acceptance probes. The judge preferred the candidate because it caught an additional mutation-before-output defect while using less test surface, fewer review rounds, and less wall time.
- Aggregate normalized cost: baseline 20 test functions, 1,017 added test lines, 7 full review rounds, and 7,529 seconds; candidate 13 test functions, 448 added test lines, 3 full review rounds, and 3,563 seconds.
- Candidate field compliance passed. The hard cost gate also found strict improvement on both pre-registered axes: unjustified permanent decisions `4 -> 0` and unnecessary full rereviews `3 -> 2`.
- The unchanged outcome ledger rejected RF-001 and RF-003 because the candidate recorded `full` where `targeted` was required. RF-001 was escalated through the separate `public_contract` flag; RF-003 was also treated as a public diagnostic/no-write contract change.
- Per the no-tuning rule, v7 stops as `candidate_regression` despite the favorable blind verdict and cost improvements. A further rule change would require a separately approved v8.
- Preserved artifacts: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v7/results/`.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v7.md
baseline_ref: a4116bb
candidate_ref: 3b07ee8
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
