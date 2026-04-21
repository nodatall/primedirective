# Sub-task Contract: 2.2

goal: Update downstream TDD, task generation, and improve-plan contracts to preserve and audit research-backed decisions.

in_scope:
- Update `skills/shared/references/planning/create-tdd.md`.
- Update `skills/shared/references/planning/generate-tasks.md`.
- Update `skills/shared/references/planning/improve-plan.md`.
- Require compact durable research-backed rationale in existing TDD sections.
- Require tasks-plan generation to verify completion stamp, stop on `evidence_bar_met: no`, and carry adopted implementation-impact findings into tasks.
- Require improve-plan to audit Evidence Ledger, Finding-to-Artifact Delta, Completion Stamp, and stop rather than improve around a failed stamp.

out_of_scope:
- Do not update `deep-research.md`, Pro, plan-work, task-file-contract, or plan-refine in this slice.

surfaces:
- `skills/shared/references/planning/create-tdd.md`
- `skills/shared/references/planning/generate-tasks.md`
- `skills/shared/references/planning/improve-plan.md`

acceptance_checks:
- TDD rules require research-backed rationale inside relevant existing sections, including decision, why it matters, source IDs or links, and affected `TDR-*`.
- Task generation checks completion stamp and hard-stops when `evidence_bar_met: no`.
- Task generation maps adopted implementation-impact findings to tasks or explicit deferral/non-goal.
- Improve-plan audits the structured memo and treats `evidence_bar_met: no` as incomplete planning.

reference_patterns:
- Keep the existing heading structure. Add concise bullets to current `--deep-research` sections.

test_first_plan:
- Documentation-only change; failing-first automated test is not practical. Use targeted `rg` checks after editing.

verify:
- `rg -n "research-backed rationale|completion stamp|evidence_bar_met: no|Finding-to-Artifact Delta|Evidence Ledger|adopted.*finding" skills/shared/references/planning/create-tdd.md skills/shared/references/planning/generate-tasks.md skills/shared/references/planning/improve-plan.md`
- `git diff --check -- skills/shared/references/planning/create-tdd.md skills/shared/references/planning/generate-tasks.md skills/shared/references/planning/improve-plan.md`
