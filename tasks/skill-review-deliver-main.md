# Deliver skill comparison

The expanded comparison completed on November 16, 2026 with verdict `candidate_neutral`. The revised instructions show a repeatable reuse advantage in one task family. The sample shows mixed readability preferences and no demonstrated reduction in maintenance work across tasks.

Invocation `$skill-review skill=deliver --preserve-review-artifacts`.

The baseline is commit `072db1c82252738a02ba5b256cef179a5ad6623e`. The candidate is the November 13 working-tree change to `skills/deliver/SKILL.md` and `skills/deliver/references/worker-packet.md`. Its owner files match the frozen candidate used in the original pilot and expanded runs. Kickoff on November 16 was on `main` with those two owner edits and this untracked comparison document already present. This pass updated comparison evidence.

The candidate adds guidance to find the behavior owner and callers, reuse compatible rules, prefer code a maintainer can trace and safely change, and verify the caller-observable result. Existing workflow stages and shared test-disposition rules are preserved in the compared contracts.

Four constructed requests use snapshots of actual TrueCut and WooStats source and existing tests. The source worktree snapshots and hashes are preserved with commit pointers `9379e6c26844a41f8c9aad0828825f017289d44b` and `e358df9addc005308954b6d67efe6e3f0386d81a`. They are evaluation requests rather than production roadmap commitments.

| Task | Repeated comparison findings |
| --- | --- |
| TrueCut receivables summary | Both reuse decimal arithmetic and the existing overdue rule. One baseline output has clearer durable examples of rounding and input preservation. |
| TrueCut signed-duration repair | Both repair the same shared formatter and preserve the web consumer. Both repetitions and follow-ups are equivalent. |
| WooStats cache preview | Both reuse the strict preparation/initialization owner. One baseline output has clearer durable examples of initialization side effects. |
| WooStats partial counters | Candidate centralizes the numeric validation rule in both repetitions. One candidate implementation couples complete and partial field sets, requiring a small extraction when a patch-only field is added later. |

Each task was implemented twice per version by fresh executors with the same selected model and high reasoning, producing sixteen original outputs and eight paired comparisons. Inputs, version assignments and follow-up requests were fixed before executor outputs were inspected. Independent checks were written from the requirements before source inspection. Source snapshots, allowed tools and stop boundaries were the same within each pair. Reviewers saw anonymous A/B outputs. Follow-up edit order alternated by repetition.

| Dimension | Revised preferred | Original preferred | Equal |
| --- | ---: | ---: | ---: |
| Correctness | 0 | 0 | 8 |
| Suitable reuse | 2 | 0 | 6 |
| Readability/traceability | 2 | 2 | 4 |
| Initial overall deliverable | 1 | 2 | 5 |
| Concrete follow-up work | 0 | 1 | 7 |

These counts describe paired agent judgments. The two reuse wins share the same underlying counter-validation problem. Revised readability wins concern common production-rule ownership. Original readability wins concern executable examples beside otherwise equivalent production code. The follow-up advantage concerns localized field-set evolution in one implementation. LOC, test totals, prose volume and sequential editing speed were excluded as standalone quality metrics.

All sixteen original outputs passed the frozen behavior checks and existing suites. TrueCut outputs also passed the shared typecheck. All sixteen final follow-up copies passed their checks. Follow-ups added a due-today total, signed delta formatting, changed-cache-key preview and a patch-only optional counter. Passing checks and observed edit locality support the scoped comparison. They do not provide a measured labor saving or long-term human-maintenance result.

A review setup mistake exposed gated follow-up checks and skipped-case names in the first initial-review packets. Implementation runs were unaffected. Eight fresh reviewers repeated the initial judgments using source-identical packets with future cases and their names removed. Superseded initial judgments are excluded from the final initial-result counts. The completed follow-up edits and validation evidence are retained separately. Judge command/reporting errors and an expected check on an unedited follow-up copy are preserved in their reports and excluded from implementation scoring. The correction is documented in `review-setup-correction.md`.

The final fresh auditor recorded `candidate_neutral`, no material skill regression findings, and readiness for ordinary merge-review. The sample establishes neither a consistent cross-task improvement nor a general causal effect of the new wording. Individual adverse results remain part of the evidence. The changed instructions fit the existing Deliver execution/worker-packet owners.

This evaluates bounded implementation and verification, including an actual formatter defect. Full Deliver activation, planning, orchestration, final-review/finalization behavior, deployed services and comprehensive red/green adherence are outside this comparison. Readability is agent-reviewed. Follow-up reviewers edited both versions sequentially, so their observations are qualitative. Two repetitions per arm on four selected tasks support a pilot conclusion rather than population-level equivalence.

Required skill-review references were read, including contract ownership, finding disposition, review protocol and reasoning budget. Baseline and candidate contracts were reconstructed, and raw scenario outputs preserved. The final audit verified all original-output hashes, frozen-input hashes and check-source hashes. Corrected source/test packets match the originals. Final whitespace checks passed. The skill-owner changes were reviewed on `main`.

Expanded artifacts live under `agent-scratch/skill-review/deliver-main/expanded-2026-11-16/`. The key records are `operator-manifest.json`, `requests.json`, `followups.json`, `corrected-aggregate-results.json`, `original-check-summary.json`, `followup-check-summary.json`, `parent-final-validation.json`, `final-audit.md` and `final-audit.json`. Original executors are under `runs/`. Corrected anonymous initial reviews are under `clean-initial/`. Follow-up patches and reports are under `blind/`. The earlier two-task pilot is preserved as `initial-pilot-record.md` and its original artifacts remain in the parent directory. Its narrow JSON-correctness win is separate from this expanded sample.

Detailed artifacts are preserved locally under the gitignored scratch directory. This tracked document preserves the comparison summary.

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: deliver
state_doc: tasks/skill-review-deliver-main.md
baseline_ref: 072db1c82252738a02ba5b256cef179a5ad6623e
candidate_ref: agent-scratch/skill-review/deliver-main/expanded-2026-11-16/candidate
scenario: four repository-derived tasks with two repetitions per version
baseline_run_complete: yes
candidate_run_complete: yes
comparable_inputs: yes
judge_run_complete: yes
judge_blinded: yes
verdict: candidate_neutral
artifact_evidence_preserved: yes
ready_for_merge_review: yes
stop_reason: neutral_no_regression
