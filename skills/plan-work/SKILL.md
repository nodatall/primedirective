---
name: plan-work
description: Turn a source plan or request into `prd`, `tdd`, and `tasks-plan` artifacts. Supports rich-plan intake, Socratic refinement, `--grill`, `--deep-research`, and `--preserve-planning-artifacts`.
---

# Plan Work Skill

Execute planning only. Do not write implementation code.

## Activation

Invoke explicitly with `$plan-work`.

Supported modifiers:

- `--grill`
- `--deep-research`
- `--preserve-planning-artifacts`

Treat the current user request as the planning payload. It may be a sparse idea or a fully fleshed-out source plan. Default to rich-plan intake unless the request is clearly sparse.

## Required references

Load these files before running:

- `skills/shared/references/planning/socratic-planning.md`
- `skills/shared/references/planning/deep-research.md`
- `skills/shared/references/planning/create-prd.md`
- `skills/shared/references/planning/create-tdd.md`
- `skills/shared/references/planning/generate-tasks.md`
- `skills/shared/references/planning/improve-plan.md`
- `skills/shared/references/execution/task-file-contract.md`

## Workflow

1. Run planning preflight from `socratic-planning.md`.
   - If the agent is currently in collaboration `Plan` mode, alert the user to exit back to collaboration `Default` mode and stop immediately.
   - Do not ask planning questions or generate artifacts while that mode guard is active.
2. Intake the source material, classify it as rich source plan or sparse source prompt, and normalize it into `Goal`, `Context`, `Constraints`, and `Done when`.
3. Run the Socratic refinement loop:
   - one question per turn
   - plain language
   - for each question, provide a recommended answer or default
   - gap-check, contradiction-check, and assumption-check only
   - for any non-trivial plan, ask at least one user-facing question before document generation
   - for non-trivial rich plans, ask at least two user-facing questions before document generation unless repo exploration resolves one branch without user input
   - for non-trivial rich plans touching infrastructure, deployment, scheduling, source-of-truth, or operations, at least one of those questions must be a targeted challenge question before document generation
   - with `--grill`, keep walking materially dependent decision branches until implementation-affecting ambiguity is resolved rather than stopping at the first acceptable draft shape
   - close gaps in `Goal`, `Context`, `Constraints`, and `Done when` before document generation
   - produce a final plain-language summary that a 12-year-old could follow, in exactly three short paragraphs
4. Only after the required question floor has been satisfied and answered, generate an initial `tasks/prd-<plan-key>.md` draft using `create-prd.md`.
5. Generate an initial `tasks/tdd-<plan-key>.md` draft using `create-tdd.md`.
6. If `--deep-research` is present, run `deep-research.md` against the locked decisions plus the source plan and current PRD/TDD drafts, then revise PRD/TDD with the adopted findings.
7. Present that three-paragraph summary to the user as a standalone checkpoint before task generation and ask if anything is wrong or missing.
8. If the user corrects the summary, resolve the correction in PRD/TDD before continuing.
9. Generate `tasks/tasks-plan-<plan-key>.md` using `generate-tasks.md`.
10. Run `improve-plan.md` once against the source plan plus all generated artifacts, plus the research memo when preserved.
11. Stop and wait for implementation trigger.

## Planning rules

- Always produce all three planning artifacts.
- Do not use lean-mode branching. Simpler work produces shorter docs naturally.
- Do not leave `Open questions` or `Open technical questions` in final artifacts.
- Do not treat the summary checkpoint as a substitute for the required question turns.
- Do not draft PRD, TDD, or tasks-plan before the required question floor and any required challenge question have been satisfied.
- Preserve substantive source-plan sections; normalize them without dropping content.
- Make repo-local implementation or test patterns explicit in the generated artifacts when relevant examples already exist; record what should be followed instead of inventing a new pattern by default.
- Inspect the target repo's existing validation/tooling surface during planning: manifests, scripts or task runners, CI workflows, lint or format configs, typecheck or build configs, and git hook setup.
- If a question can be answered from the repo, inspect the repo instead of asking the user.
- Do not silently choose material defaults before asking at least one relevant question, unless the user explicitly asks for a faster default-driven planning pass.
- With `--grill`, bias against early convergence: ask the next material question when an answer creates a new implementation, operational, verification, data-shape, or UX branch.
- With `--grill`, do not stop after one good answer if a dependent branch remains unresolved.
- With `--grill`, avoid cosmetic or repetitive questioning; keep the pressure on decisions that would change design, sequencing, scope, verification, or ownership.
- If the target repo lacks meaningful validation or formatting enforcement for its stack, make that gap explicit in PRD, TDD, and tasks-plan instead of assuming those checks exist.
- When planned work would materially benefit from missing validation tooling, add explicit bootstrap work for the config files, scripts, CI wiring, and hook integration needed for that repo before downstream feature tasks rely on them.
- When the missing validation/tooling should be installed as first-time repo setup, make the earliest bootstrap task executable via `$bootstrap-repo-rules [--with-hooks]`.
- Make expected red/green ownership explicit in the generated artifacts: identify which planned sub-tasks should begin with a failing targeted test first, and note only the slices that are expected to need a justified exception.
- With `--deep-research`, research defaults to `Tech + Delivery`: technical design, migration/rollout/rollback, security/ops, and verification strategy.
- With `--deep-research`, live web research is mandatory and the working memo must include at least 5 substantive external primary web sources.
- With `--deep-research`, the research framing must include the exact current date and the plan-specific stack, constraints, and quality priorities before web research begins.
- With `--deep-research`, record source freshness metadata for substantive external sources and distinguish adopt-now guidance from emerging or avoid guidance.
- With `--deep-research`, PRD and TDD may be drafted before research, but treat them as interim drafts until the research memo and completion checks from `deep-research.md` are complete and adopted findings are applied back into both documents as needed.
- With `--deep-research`, do not proceed if live web research is unavailable; stop and tell the user the deep-research pass cannot run without web access.
- With `--deep-research`, do not begin `tasks-plan` drafting until the research memo is complete and PRD/TDD have been revised from the adopted findings.
- `--deep-research` should influence TDD and tasks-plan first; update PRD only when product constraints or defaults materially change.
- With `--deep-research`, end the memo with a plan-specific checklist or implementation guidance section so the adopted findings are easy to carry into execution for this plan.
- With `--preserve-planning-artifacts`, keep `tasks/tmp/research-plan-<plan-key>.md` and mention it in the final planning summary.
- Restore traceability from tasks to `FR-*` and `TDR-*` IDs.

## UI behavior

Prefer structured dialog questions when client supports them. Fallback to plain-text one-question turns when not supported.

## Hard gate

After planning is complete, wait for explicit `$execute-task` activation:

- standard mode with a specific `<task-id>` and `<plan-key>`
- one-shot mode with a specific `<plan-key>`

Do not start coding from planning flow.
