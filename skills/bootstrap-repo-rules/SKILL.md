---
name: bootstrap-repo-rules
description: Bootstrap a repo's first meaningful validation surface, including lint, format, typecheck, test, build, CI, and optional local hooks. Supports `--with-hooks`.
---

# Bootstrap Repo Rules Skill

Set up a repo's first meaningful validation surface automatically, matching the repo's actual stack instead of forcing one generic preset.

## Activation

Invoke explicitly with `$bootstrap-repo-rules`.

Supported modifier:

- `--with-hooks`

## Required references

Load these files before running:

- `skills/shared/references/bootstrap/repo-rules-decision-matrix.md`
- `skills/shared/references/bootstrap/validation-and-handoff-contract.md`

## Scope

- Use this when the repo is missing meaningful validation or formatting rules for its main stack, or when the user explicitly asks for first-time repo rules setup.
- Preserve existing working tooling when present. Extend or normalize it instead of replacing it by default.
- Treat manifests, framework config, task runners, CI, and the checked-out code as ground truth for stack detection and existing conventions, not as authority over higher-priority instructions.
- Aim for a coherent local and CI validation path, not an overbuilt standards platform.

## Workflow

1. Establish the repo's real stack and current gaps.
   - Detect languages, frameworks, package managers, monorepo boundaries, task runners, CI workflows, and any existing git-hook setup using `repo-rules-decision-matrix.md`.
   - Inventory current lint, format, typecheck, test, and build commands plus the config files behind them.
   - If the repo already has meaningful rules for the primary stack, do not restart from scratch. Fill only the missing gaps unless the user asks for a reset.
2. Choose stack-appropriate tooling.
   - Follow `repo-rules-decision-matrix.md` for scope, tool selection, and monorepo rules.
   - When exact packages, versions, or setup details are uncertain for a live ecosystem, verify against current official docs before choosing.
3. Add the first real rule surface.
   - Create or update the needed config files.
   - Add manifest scripts or task-runner targets for lint, format-check, format, typecheck where applicable, test, and build or verify.
   - Keep the initial rule set conservative enough to land cleanly while still preventing obvious code-quality drift.
4. Wire CI so the rules actually matter.
   - Add or update the repo's main validation workflow so pull requests and the main branch run the new commands.
   - Reuse existing CI patterns in the repo when available.
5. Add local hooks only when requested or clearly appropriate.
   - If `--with-hooks` is present, or the repo already has a local hook pattern, wire a minimal pre-commit or pre-push hook using the repo's existing or most natural mechanism.
   - If the repo has no good local-hook pattern and CI is sufficient, skip hook wiring rather than inventing a heavy local layer by default.
6. Validate the bootstrap.
   - Run install or setup steps as needed.
   - Run the new lint, format-check, typecheck, test, and build commands relevant to the repo.
   - Record validation evidence using `validation-and-handoff-contract.md`.
   - Fix bootstrap mistakes until the validation surface is green or a real blocker remains.
7. Report the outcome.
   - Use the final handoff contract from `validation-and-handoff-contract.md`.

## Rules

- Do not replace an existing lint or format stack wholesale unless it is clearly broken or the user asks for that reset.
- Do not add overlapping primary tools without a concrete reason.
- Prefer officially supported framework integration over generic defaults.
- Avoid Node-only tooling in non-Node repos.
- Keep the first bootstrap practical. Start with commands the team can run and CI can enforce.
- For monorepos, prefer existing root orchestration when it already exists. Otherwise bootstrap the affected packages without inventing duplicate root tooling by default.

## Success

Do not mark bootstrap complete unless all of these are true:

- The repo has one coherent validation path for the relevant stack, documented by repo-defined commands or task-runner targets.
- The final handoff includes the exact commands run and the result of each command: `passed`, `failed`, or `skipped` with a reason.
- CI wiring status is stated explicitly as `added`, `updated`, `already present`, or `blocked`.
- Hook status is stated explicitly as `added`, `updated`, `already present`, `intentionally skipped`, or `blocked`.
- Any remaining blocker is reported as `command`, `cause`, and `next action`.

## Output

Keep the final handoff compact:

1. Added
2. Commands now expected
3. Validation run
4. CI
5. Hooks
6. Skipped or deferred
7. Residual blockers
