---
name: bootstrap-repo-rules
description: Use when the user requests `bootstrap repo rules [--with-hooks]` and the repo needs first-time validation tooling such as lint, format, typecheck, test or build verification, CI wiring, and optional local git-hook enforcement.
---

# Bootstrap Repo Rules Skill

Set up a repo's first meaningful validation surface automatically, matching the repo's actual stack instead of forcing one generic preset.

## Triggers

Accept:

- `bootstrap repo rules`
- `bootstrap repo rules --with-hooks`

## Scope

- Use this when the repo is missing meaningful validation or formatting rules for its main stack, or when the user explicitly asks for first-time repo rules setup.
- Preserve existing working tooling when present. Extend or normalize it instead of replacing it by default.
- Treat manifests, framework config, task runners, CI, and the checked-out code as ground truth.
- Aim for a coherent local and CI validation path, not an overbuilt standards platform.

## Workflow

1. Establish the repo's real stack and current gaps.
   - Detect languages, frameworks, package managers, monorepo boundaries, task runners, CI workflows, and any existing git-hook setup.
   - Inventory current lint, format, typecheck, test, and build commands plus the config files behind them.
   - If the repo already has meaningful rules for the primary stack, do not restart from scratch. Fill only the missing gaps unless the user asks for a reset.
2. Choose stack-appropriate tooling.
   - Follow repo-native or framework-native tooling when it already exists.
   - For JavaScript or TypeScript repos, choose one coherent primary path that fits the repo and framework instead of mixing overlapping tools by default.
   - For Python repos, prefer a single modern lint and format path when the repo has no existing standard.
   - For Go, Rust, shell, and other non-Node stacks, prefer the language-native or ecosystem-standard checks instead of forcing Node-based tooling.
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
   - Fix bootstrap mistakes until the validation surface is green or a real blocker remains.
7. Report the outcome.
   - What was added.
   - Which commands are now the repo standard.
   - Whether local hooks were added or intentionally skipped.
   - Any residual blockers or deferred rule tightening.

## Rules

- Do not replace an existing lint or format stack wholesale unless it is clearly broken or the user asks for that reset.
- Do not add overlapping primary tools without a concrete reason.
- Prefer officially supported framework integration over generic defaults.
- Avoid Node-only tooling in non-Node repos.
- Keep the first bootstrap practical. Start with commands the team can run and CI can enforce.

## Output

Keep the final handoff compact:

1. Added
2. Commands now expected
3. Hooks
4. Residual blockers
