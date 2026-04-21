# Sub-task Contract: 3.1

goal: Lock combined `--deep-research --pro-analysis` modifier order and Pro/research reconciliation.

in_scope:
- Update `skills/plan-and-execute/SKILL.md`.
- Update `skills/shared/references/execution/task-file-contract.md`.
- Preserve the current order: deep research first, revise PRD/TDD, Pro analysis as final adversarial planning pass, tasks-plan generation, refine-plan when active, execution.
- State that Pro output does not count toward the deep-research external primary-source minimum.
- State that Pro-suggested sources may influence source-backed claims only after independent main-agent verification and Evidence Ledger recording.
- Require reconciliation for Pro conflicts with research memo or repo facts.

out_of_scope:
- Do not update `deep-research.md`, `plan-refine`, or downstream task generation in this slice.

surfaces:
- `skills/plan-and-execute/SKILL.md`
- `skills/shared/references/execution/task-file-contract.md`

acceptance_checks:
- Combined modifier order is explicit and matches the source plan.
- Pro cannot replace primary evidence.
- Pro-suggested sources require independent verification before influencing source-backed claims.
- Conflicts between Pro, deep research, and repo facts require reconciliation before tasks-plan generation.

reference_patterns:
- Follow existing modifier bullets in both target files.

test_first_plan:
- Documentation-only change; failing-first automated test is not practical. Use targeted `rg` checks after editing.

verify:
- `rg -n "deep research first|Pro.*does not count|Pro-suggested|independently.*verified|Evidence Ledger|reconciliation|primary evidence" skills/plan-and-execute/SKILL.md skills/shared/references/execution/task-file-contract.md`
- `git diff --check -- skills/plan-and-execute/SKILL.md skills/shared/references/execution/task-file-contract.md`
