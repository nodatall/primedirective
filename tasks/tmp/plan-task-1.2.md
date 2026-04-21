# Sub-task Contract: 1.2

goal: Add draft-linked research agenda, Finding-to-Artifact Delta, and Deep Research Completion Stamp requirements to the deep-research contract.

in_scope:
- Update `skills/shared/references/planning/deep-research.md`.
- Require draft-linked research questions.
- Require Finding-to-Artifact Delta fields named by the PRD/TDD.
- Require Deep Research Completion Stamp fields named by the PRD/TDD.
- Define `evidence_bar_met: no` as a planning stop in the deep-research contract.

out_of_scope:
- Do not update downstream generate-tasks, improve-plan, Pro, or refine-plan contracts in this slice.

surfaces:
- `skills/shared/references/planning/deep-research.md`

acceptance_checks:
- Research questions must identify the draft assumption, PRD section, TDD section, `FR-*`, or `TDR-*` they could change.
- Finding-to-Artifact Delta contains `finding_id`, `research_question_id`, `bucket`, `disposition`, `recommendation`, `recommendation_level`, `support_type`, `source_ids`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `disposition_reason`.
- Completion Stamp contains `external_primary_sources_count`, `source_family_count`, `research_questions_answered`, `buckets_reviewed`, `follow_up_passes_completed`, `adopted_findings_count`, `rejected_or_deferred_findings_count`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `evidence_bar_met`.
- The contract says planning stops when `evidence_bar_met: no`.

reference_patterns:
- Continue the structure already added around Evidence Ledger in `deep-research.md`.

test_first_plan:
- Documentation-only change; failing-first automated test is not practical. Use targeted `rg` checks after editing.

verify:
- `rg -n "Draft-Linked Research Agenda|Finding-to-Artifact Delta|finding_id|research_question_id|disposition_reason|Deep Research Completion Stamp|evidence_bar_met|source_family_count|follow_up_passes_completed|prd_tdd_sections_changed|task_plan_inputs_created" skills/shared/references/planning/deep-research.md`
- `git diff --check -- skills/shared/references/planning/deep-research.md`
