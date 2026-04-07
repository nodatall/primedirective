# Validation And Handoff Contract

Use this reference to define when bootstrap is actually complete and how to report the outcome.

## Minimum validation surface

Run every check that is both relevant to the repo and defined or introduced by the bootstrap:

- lint
- format-check
- typecheck where applicable
- test where applicable
- build or verify where applicable

If a check is not applicable or cannot run yet, record that explicitly instead of implying success.

## Validation evidence

Capture the exact command for every check you evaluated.

Record one status per command:

- `passed`
- `failed`
- `skipped` with reason

If install or setup steps were required before validation, record those commands too.

## Completion contract

Do not mark bootstrap complete unless:

- the repo has a coherent local validation path for the primary stack
- the repo's main CI validation path is `added`, `updated`, or `already present`, or else clearly `blocked`
- hook status is reported as `added`, `updated`, `already present`, `intentionally skipped`, or `blocked`
- skipped checks are listed with a concrete reason
- each blocker is captured with `command`, `cause`, and `next action`

`Green` means all applicable required commands passed. If any applicable required command failed, do not report the bootstrap as complete.

## Final handoff shape

Keep the handoff compact and use this order:

1. `Added`
2. `Commands now expected`
3. `Validation run`
4. `CI`
5. `Hooks`
6. `Skipped or deferred`
7. `Residual blockers`

## Field requirements

### Added

- list only the config files, scripts, workflow files, or hook files that changed bootstrap behavior materially

### Commands now expected

- list the repo-standard commands the team should run locally and in CI

### Validation run

- include each executed command and its status

### CI

- state whether CI was `added`, `updated`, `already present`, or `blocked`

### Hooks

- state whether hooks were `added`, `updated`, `already present`, `intentionally skipped`, or `blocked`

### Skipped or deferred

- list checks not run yet, with a concrete reason

### Residual blockers

- for each blocker, record:
  - `command`
  - `cause`
  - `next action`
