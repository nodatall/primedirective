# Sub-task Contract: 3.1

plan_key: plan-refine-challenger-lane
task_id: 3.1

## Goal

Run text and installer validation, inspect public invocation surfaces for unintended syntax changes, then prepare planning artifacts for archive/finalization.

## In Scope

- Validation commands:
  - `git diff --check`
  - temp-home double run of `./scripts/install-codex-plugin.sh`
  - real `./scripts/install-codex-plugin.sh`
- Confirm README invocation syntax remains unchanged.
- Mark final task complete when validation passes.

## Out Of Scope

- Additional feature edits unless validation or final review finds a real issue.
- New CI/test harness creation.

## Surfaces

- Validation evidence
- `tasks/tasks-plan-plan-refine-challenger-lane.md`

## Acceptance Checks

- `git diff --check` passes.
- Installer idempotence passes in a temp home.
- Real installer runs successfully.
- README public skill invocation table still shows no new public flag/skill for this change.
- All task checkboxes are complete before archive.

## Reference Patterns

- README Verification section.
- `.github/workflows/validate.yml` installer idempotence workflow.

## Test First Plan

This is a validation-only slice; no failing-first edit is applicable.

## Verify

```bash
git diff --check
tmp_home="$(mktemp -d)" && HOME="$tmp_home" ./scripts/install-codex-plugin.sh && HOME="$tmp_home" ./scripts/install-codex-plugin.sh
./scripts/install-codex-plugin.sh
```
