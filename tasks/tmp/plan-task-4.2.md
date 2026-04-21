# Sub-task Contract: 4.2

goal: Run final full-branch review, complete the task checklist, and archive planning artifacts.

in_scope:
- Run final broad validation for the touched Markdown and installer surfaces.
- Run one fresh full-branch review against `origin/main`.
- Address any blocker/material review findings.
- Mark remaining task checkboxes complete.
- Archive PRD, TDD, and tasks-plan under `tasks/archive/2026-04-21-deep-research-contract-hardening/`.

out_of_scope:
- Do not add new feature scope beyond review fixes.
- Do not preserve temp planning/review artifacts unless required by a blocker or final process.

surfaces:
- Full branch diff versus `origin/main`.
- `tasks/archive/2026-04-21-deep-research-contract-hardening/`

acceptance_checks:
- Final validation passes.
- Final full-branch review finds no unresolved blocker/material issues.
- Active planning artifacts are moved into the archive.
- No duplicate active PRD/TDD/tasks-plan set remains under `tasks/`.

reference_patterns:
- Follow `skills/shared/references/review/review-protocol.md` full-branch review behavior.
- Follow `skills/shared/references/execution/task-management.md` archive cleanup behavior.

test_first_plan:
- Review/archive slice; failing-first automated test is not practical.

verify:
- `git diff --check && HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh && HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`
- final review log
- `find tasks/archive/2026-04-21-deep-research-contract-hardening -maxdepth 1 -type f | sort && test ! -e tasks/prd-deep-research-contract-hardening.md && test ! -e tasks/tdd-deep-research-contract-hardening.md && test ! -e tasks/tasks-plan-deep-research-contract-hardening.md`
