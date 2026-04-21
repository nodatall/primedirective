# Sub-task Contract: 3.2

goal: Prevent plan refinement from silently weakening research-backed decisions.

in_scope:
- Update `skills/plan-refine/SKILL.md`.
- Update `skills/shared/references/execution/task-file-contract.md`.
- Require plan-refine to read the research memo when available, otherwise the durable research digest in TDD, when deep research was used.
- Require plan-refine to stop on `evidence_bar_met: no`.
- Require plan-refine to preserve, explicitly supersede, or defer research-backed decisions with a recorded reason.
- Require a final research-carry-forward check after refinement.

out_of_scope:
- Do not update `deep-research.md`, Pro ordering, TDD generation, or task generation in this slice.

surfaces:
- `skills/plan-refine/SKILL.md`
- `skills/shared/references/execution/task-file-contract.md`

acceptance_checks:
- Refine-plan has an explicit deep-research-aware behavior path.
- Refinement reads `tasks/tmp/research-plan-<plan-key>.md` if it exists, otherwise reads durable research digest in TDD.
- Refinement stops on `evidence_bar_met: no`.
- Research-backed `TDR-*`, rollout, migration, rollback, verification, or task dependency changes cannot be removed/weakened without a reason.
- A final research-carry-forward check is required before execution continues.

reference_patterns:
- Follow existing plan-refine workflow and critique-standard bullet style.
- Keep task-file-contract cross-skill rules concise.

test_first_plan:
- Documentation-only change; failing-first automated test is not practical. Use targeted `rg` checks after editing.

verify:
- `rg -n "research-backed|research memo|durable research digest|superseded|evidence_bar_met: no|final research-carry-forward" skills/plan-refine/SKILL.md skills/shared/references/execution/task-file-contract.md`
- `git diff --check -- skills/plan-refine/SKILL.md skills/shared/references/execution/task-file-contract.md`
