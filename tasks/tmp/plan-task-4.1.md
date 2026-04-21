# Sub-task Contract: 4.1

goal: Run focused text checks and installer smoke checks for the deep-research contract hardening changes.

in_scope:
- Run final text validation commands.
- Run temporary-home installer smoke checks.
- Do not change source files unless a validation failure identifies a concrete in-scope issue.

out_of_scope:
- Do not archive planning artifacts in this slice.
- Do not run final full-branch review in this slice.

surfaces:
- Validation commands only, unless a focused fix is required.

acceptance_checks:
- `git diff --check` passes.
- `HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh` passes.
- `HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh` passes.

reference_patterns:
- README verification section lists installer smoke checks.
- `.github/workflows/validate.yml` validates Codex installer idempotence.

test_first_plan:
- Validation-only slice; no failing-first edit loop is practical unless a command fails.

verify:
- `git diff --check && HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh && HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`
