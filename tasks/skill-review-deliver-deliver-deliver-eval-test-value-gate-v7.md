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

- [ ] Implement the schema, validator, owner wording, mirrors, and focused tests.
- [ ] Validate and forward-test the candidate.
- [ ] Run a fresh adversarial implementation review and install the exact candidate.
- [ ] Commit and record the exact candidate ref.
- [ ] Run the four-arm frozen comparison and blind judge.
- [ ] Apply candidate compliance and the unchanged hard outcome gate.
- [ ] Preserve artifacts and record the final verdict without in-run tuning.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-deliver-deliver-eval-test-value-gate-v7.md
baseline_ref: a4116bb
candidate_ref: pending
scenario: evals/deliver/suite.md
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: yes
ready_for_merge_review: no
stop_reason: missing_candidate
