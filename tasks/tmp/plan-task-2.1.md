# Sub-task Contract: 2.1

goal: Keep the deep-research memo available through downstream planning audits before cleanup.

in_scope:
- Update `skills/plan-work/SKILL.md`.
- Update `skills/shared/references/execution/task-file-contract.md`.
- Make clear that `improve-plan.md` receives the research memo whenever `--deep-research` was used.
- Make clear that normal memo cleanup happens after `improve-plan`, and after `plan-refine` when `$plan-and-execute --refine-plan` is active.

out_of_scope:
- Do not update `deep-research.md`, TDD generation, task generation, Pro, or refine-plan guardrails in this slice.

surfaces:
- `skills/plan-work/SKILL.md`
- `skills/shared/references/execution/task-file-contract.md`

acceptance_checks:
- `plan-work` no longer says improve-plan receives the research memo only when preserved.
- The task-file contract states memo retention through improve-plan and plan-refine where applicable.
- Cleanup/preservation wording still preserves the existing behavior that temp files are deleted unless preservation was requested, after required audits complete.

reference_patterns:
- Follow existing modifier sections in `skills/shared/references/execution/task-file-contract.md`.
- Keep `skills/plan-work/SKILL.md` workflow concise.

test_first_plan:
- Documentation-only change; failing-first automated test is not practical. Use targeted `rg` checks after editing.

verify:
- `rg -n "research memo.*improve-plan|until.*improve-plan|until.*plan-refine" skills/plan-work/SKILL.md skills/shared/references/execution/task-file-contract.md`
- `git diff --check -- skills/plan-work/SKILL.md skills/shared/references/execution/task-file-contract.md`
