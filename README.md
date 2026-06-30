# Prime Directive

Prime Directive is my personal skill library.

It is a set of workflows I use every day with Codex, Claude, and other coding agents. Most of it is engineering workflow: planning, implementation, review, architecture, deep research, first-principles analysis, model escalation, performance optimization, branch shipping, and a few writing helpers.

## Paste Install

Open Codex or Claude in any repo and paste:

```text
Install Prime Directive: clone https://github.com/nodatall/primedirective.git into ~/.prime-directive/repo if it is missing, otherwise pull latest there. Then run ~/.prime-directive/repo/setup --host auto. Do not vendor Prime Directive's skills/ tree into this project. After install, tell me which Prime Directive skills are available and ask whether I want team mode for this repo.
```

Equivalent shell:

```bash
if [ ! -d "$HOME/.prime-directive/repo/.git" ]; then
  git clone --depth 1 https://github.com/nodatall/primedirective.git "$HOME/.prime-directive/repo"
fi
cd "$HOME/.prime-directive/repo" && git pull --ff-only && ./setup --host auto
```

The installer detects the host. For Codex, it registers the local plugin and symlinks the skills into `~/.codex/skills/`. For Claude, it symlinks the skills into `~/.claude/skills/`. Re-run `./setup --host auto` after pulling updates.

## Skill Quick Reference

Use the table to pick the skill. Deep research is a mode inside `$deliver` and `$first-principles-mode`; it is not a separate public skill.

The skills are composable. `$deliver` is the main orchestration workflow, and several other skills or references are smaller pieces it can use: `$plan-to-goal` when the work is really a long-running goal, `$review-plan` when the user asks for an adversarial plan review before implementation, deep research and Pro analysis as optional planning passes, and shared review/finalization contracts during closeout. Other skills, such as `$review-chain`, `$repo-sweep`, and the optimizer skills, can stand alone but use the same style of focused review, evidence, and stop conditions.

| Skill | What it does |
| --- | --- |
| `deliver` | Use `$deliver` for the main planning, implementation, and review workflow. After you talk through what you want to build, it turns the conversation into a plain Markdown plan with checkboxes, optionally runs `--deep-research` or `--pro-analysis`, improves the plan, shows it for review, then implements it task by task with focused subagents, commits, validation, and final review. Use `--fast` only when you want to skip the initial plan-review pause. |
| `clarifier` | Use `$clarifier` when you want help turning a rough draft or stuck thought into clearer writing by revising it yourself with questions and short teaching examples. |
| `plain-language` | Use `$plain-language` when you want a shorter, clearer, plainer answer or rewrite. |
| `plan-to-goal` | Use `$plan-to-goal [plan-key=<plan-key>]` when a rough goal prompt, thread plan, readable execution plan, or PRD/TDD/tasks-plan set should become a reviewable goal-plan doc with an embedded copy-pasteable `/goal` start prompt. |
| `first-principles-mode` | Use `$first-principles-mode` when the main need is deep read-only analysis, not edits. It uses a default adversarial council with independent lanes and rebuttal rounds, checks load-bearing claims, and supports `--deep-research` and `--pro-analysis`. |
| `deep-research-prompt` | Use `$deep-research-prompt` when you want a paste-ready ChatGPT.com Deep Research prompt from the current thread before local planning or execution. It asks for a load-bearing falsification pass and says to revise the conclusion when the evidence breaks. |
| `repo-sweep` | Use `$repo-sweep` when you want a broad repository audit and production-readiness pass; use `/goal $repo-sweep` when you want the repair/resweep loop. Supports `--pro-analysis`, `--swarm`, `--dep-scan`, and `--preserve-review-artifacts`; `--swarm` includes nitpick depth. |
| `ship-branch` | Use `$ship-branch` when the current feature branch should be pushed, PR'd, merged, deleted locally/remotely, and the checkout returned to the base branch. |
| `page-speed-optimizer` | Use `$page-speed-optimizer` when the work is specifically frontend journey speed: page load, Core Web Vitals, interaction responsiveness, route transitions, flashes, layout shifts, bfcache/back-forward behavior, frontend assets, third-party cost, or browser-perceived performance. Bare `$page-speed-optimizer` is report-first; use `/goal $page-speed-optimizer` for the bounded measured fix loop. |
| `test-suite-optimizer` | Use `$test-suite-optimizer` when the work is specifically test-suite or CI feedback speed: slow tests, setup/teardown cost, runner configuration, flaky tests that cause reruns, coverage/report cost, CI caches, artifacts, sharding, or parallelism while preserving validation confidence. Bare `$test-suite-optimizer` is report-first; use `/goal $test-suite-optimizer` for the bounded measured fix loop. |
| `backend-optimizer` | Use `$backend-optimizer` when the work is specifically backend or database performance: exhaustive query sweeps, schema/index health, backend runtime cost, or operational database hygiene. Bare `$backend-optimizer` is report-first; use `/goal $backend-optimizer` for the bounded measured fix loop. |
| `review-chain` | Use `$review-chain` when you want a branch or task reviewed without a repo-wide sweep. Supports `--preserve-review-artifacts` and an optional task ID in the request for task-scoped review. |
| `merge-review` | Use `$merge-review` inside `/goal $merge-review` when the current branch should be made merge-ready through a review/fix/validate/rereview loop. |
| `review-plan` | Use `$review-plan [plan-key=<plan-key>]` when an active `$deliver` execution plan should get an adversarial first-principles council pass before implementation. Supports `plan-key=<plan-key>` and `--approval-gate`. |
| `plan-refine` | Use `$plan-refine [plan-key=<plan-key>]` only for legacy PRD/TDD/tasks-plan artifacts that need pressure testing before being converted into `$deliver` or a goal. Supports `plan-key=<plan-key>`, `--max-rounds=<n>`, and `--preserve-refine-artifacts`; max rounds default to 8 and are capped at 8. |
| `skill-review` | Use `$skill-review [skill=<skill-name>]` before merging Prime Directive skill changes when you want evidence that the candidate skill contract works better in practice. Supports `skill=<skill-name>`, `scenario=<path-or-name>`, `baseline=<git-ref>`, `candidate=<git-ref-or-worktree>`, and `--preserve-review-artifacts`. |
| `create-architecture` | Use `$create-architecture` when a non-trivial repo needs a concrete `docs/ARCHITECTURE.md`, or before boundary-affecting work when that file is missing. |
| `bootstrap-repo-rules` | Use `$bootstrap-repo-rules` when a repo needs its first meaningful validation, formatting, build, test, or CI surface. Supports `--with-hooks`. |
| `cleanup-merged-branches` | Use `$cleanup-merged-branches` when you want safe local and remote cleanup of merged branches. You can include a branch name to inspect only that branch. |

## Skill Details

### `$deliver`

Modifiers:

- `--deep-research`: run web-backed operator/current-practice research after the readable execution plan exists, synthesize adopted findings into the plan, then continue to Pro analysis when requested or refinement when not.
- `--pro-analysis`: run ChatGPT Pro browser escalation after the readable execution plan exists, synthesize findings into the plan, then refine and ask the user to review the Markdown file only after the Pro synthesis gate succeeds.
- `--deep-research --pro-analysis`: run deep research first, apply adopted findings to the execution plan, then run ChatGPT Pro against the researched plan before refinement.
- `--fast`: skip only the initial plan-review pause after refinement, then start implementation immediately; validation, final review, archive, commit, and finalization still run.

`$deliver` is the main packaged workflow for planning, implementation, and review.

It is also a composition point. It does not try to keep every behavior in one giant prompt. It calls or loads smaller skill contracts and references at the moment they are needed: `$plan-to-goal` for goal-shaped work, `$review-plan` for requested pre-implementation plan critique, deep research for web-backed evidence, Pro analysis for high-reasoning plan pressure, worker packets for implementation subagents, review protocol for final review, and the finalization gate before handoff.

The normal flow starts with freeform conversation. You talk with the agent until the work is clear enough, then say `deliver`. The skill takes the whole conversation and turns it into one readable execution plan refined right away. The plan is simple, plain-language, saved on disk, and built around checkboxes so the work can be reviewed, resumed, and finished deliberately.

When the work needs an adaptive loop instead of a normal execution plan, `$deliver` can route to a goal-plan prompt for adaptive evidence loops.

The plan can include extra review before the user sees it. It runs web-backed deep research when requested. With `--pro-analysis`, a Codex user can have the workflow use the ChatGPT web UI to ask a high-reasoning model to review the plan. Research and Pro feedback are automatically integrated back into the plan.

After that, the agent runs a self-improvement loop over the plan: ask what can be improved, make the change, and repeat until there are no material improvements left. It asks the user to review the Markdown plan file unless `--fast` is present. The user can then go back and forth with the agent until the plan looks right. For frontend-facing plans, it creates a simple linked HTML mockup before approval so the user can see the expected visual direction.

Once the user says `implement`, the orchestrator works through the checklist. It packages one small task and the needed context for a subagent, waits for that task to finish, pulls the work back in, validates it, commits useful progress, updates the plan, and moves to the next checkbox. Implementation is sequential by default because broad parallel execution gets messy; the orchestrator may only run work in parallel when it is clearly safe.

When every checkbox is done, `$deliver` runs final review. That review is also handled through focused subagents: each reviewer gets a targeted review job, reports back, and the orchestrator records the findings. The workflow fixes what should be fixed, validates again, commits the review work, archives the plan artifacts, and performs the finalization checks before handoff.

Use bare `$deliver`, `refine`, or `plan`: keep the active checklist in `tasks/execution-plan-<plan-key>.md`, replace any draft instruction with the Deliver implementation instruction, refine it, and ask the user to review the Markdown file before approving implementation unless `--fast` is present.

Use `$deliver discuss` only when you want a draft checklist to stay current while you talk through it. `discuss` is a legacy alias for creating or updating the same draft checklist plan. Do not treat it as a separate workflow.

### `$clarifier`

Coaches revision for rough drafts, stuck thoughts, posts, essays, messages, and explanations. It restates the intended meaning, identifies one clarity issue, asks focused questions, may show one short annotated teaching example, and asks the user to write the next version themselves.

### `$plain-language`

Produces a shorter, clearer, more direct explanation or rewrite.

### `$plan-to-goal`

Request context:

- `plan-key=<plan-key>`: build the goal plan from an existing PRD/TDD/tasks-plan set.
- Source material in the thread: build the goal plan from the current conversation, rough goal prompt, diagnosis, recommendation text, or pasted plan.

Converts messy source material, rough goal prompts, readable execution plans, or PRD/TDD/tasks-plan artifacts into `tasks/goal-plan-<plan-key>.md`, with an embedded copy-pasteable `/goal` start prompt that references that file. Before writing the file, it optimizes rough prose into a first-screen `Goal`, `Done When`, `Not Done Yet If`, and `Start Prompt` block, then fills in the plain-language summary, starting evidence, target/baseline, work loop, primary verifier, supporting checks, measurable acceptance criteria, anti-cheat criteria, explicit stop conditions, boundaries, and resume state. The goal plan includes target/baseline guidance when metrics exist, finish-line-first review guidance, state-recording guidance for long runs, and no-early-stop guidance.

### `$first-principles-mode`

Modifiers:

- `--deep-research`: add web-backed operator/current-practice research with an evidence bar.
- `--pro-analysis`: escalate through the ChatGPT Pro browser wrapper and synthesize the result back into the local analysis.

Runs a deep, read-only analysis pass. It is for mechanism-level judgment, competing explanations, root-cause reasoning, or plan critique before deciding what to build or change. It uses a default adversarial council with independent lanes and rebuttal rounds before synthesis. It gives extra falsification effort to load-bearing claims that would change the conclusion, confidence, or next verification step if wrong. When the evidence cannot separate plausible explanations, it should stop and name the smallest verification step needed next.

### `$deep-research-prompt`

Creates a paste-ready prompt for ChatGPT.com Deep Research from the current thread. It assumes you will manually select the relevant GitHub repo, files, or project context in ChatGPT before starting the research.

The generated prompt asks Deep Research to end with a load-bearing falsification pass: test the claims that would change the recommendation if wrong, search for counterevidence when needed, and revise the conclusion when the evidence breaks.

### `$repo-sweep`

Modifiers:

- `--pro-analysis`: use ChatGPT Pro browser escalation as Round 1 audit-thesis input.
- `--swarm`: add parallel read-only discovery lanes for intent/regression, security/privacy, performance/reliability, contracts/coverage, and nitpick-depth maintainability/code-quality review before the report.
- `--dep-scan`: run an explicit dependency and supply-chain audit, reporting unavailable scanners as residual risk.
- `--preserve-review-artifacts`: keep sweep/review logs instead of cleaning them after success.

Runs a broad repository audit. It starts with first-principles no-edit analysis, runs review/security/production-readiness checks, reports findings, and pauses before fixes. Invoke `/goal $repo-sweep` for the bounded repair/resweep loop.

### `$ship-branch`

Finishes the current feature branch. It handles dirty work first by showing a compact status/diff summary and asking whether to commit or stash, prefers the repo's explicit local merge gate when present, then pushes the branch, creates or reuses a PR, waits for pending or queued required checks, fixes actionable check failures with focused commits, merges the PR, deletes the remote branch, switches back to the base branch, pulls the merged base, and deletes the local branch.

### `$page-speed-optimizer`

Improves real user-perceived frontend journey speed and visual continuity with measured evidence. It is narrower than `$repo-sweep`: use it for page loads, in-session navigation, interaction responsiveness, Core Web Vitals, visual transition quality, frontend assets, third-party scripts, bfcache behavior, and deployed browser-performance surfaces, not for backend query optimization or broad production-readiness review.

Bare `$page-speed-optimizer` is report-first: it inventories journeys, ranks candidates, measures where practical, and recommends fixes before stopping for approval. Invoke `/goal $page-speed-optimizer` when safe measured fixes should proceed in a bounded loop until every high-impact page, transition, interaction, asset, third-party, or deploy/cache candidate is improved, rejected with evidence, or gated behind a clear decision.

### `$test-suite-optimizer`

Improves test-suite runtime and CI feedback speed with measured evidence while preserving validation confidence. It is narrower than `$repo-sweep`: use it for slow tests, setup/teardown cost, runner configuration, flaky tests that cause reruns, coverage/report cost, CI caches, artifacts, sharding, and parallelism, not for broad repository audit or generic failing-test repair.

Bare `$test-suite-optimizer` is report-first: it inventories commands, runners, CI jobs, timing sources, coverage/reporting, services, fixtures, and flakes; ranks candidates; measures where practical; and recommends fixes before stopping for approval. Invoke `/goal $test-suite-optimizer` when safe measured fixes should proceed in a bounded loop until every high-impact test, harness, coverage, flake, or CI feedback candidate is improved, rejected with evidence, or gated behind a clear decision.

### `$backend-optimizer`

Improves backend and database performance with measured evidence. It is narrower than `$repo-sweep`: use it for query performance, schema/index health, backend runtime cost, and operational database hygiene, not for broad security, architecture redesign, frontend performance, dependency audit, or whole-repo production-readiness review.

Bare `$backend-optimizer` is report-first: it inventories, ranks, measures where practical, and recommends fixes before stopping for approval. Invoke `/goal $backend-optimizer` when safe measured fixes should proceed in a bounded loop until every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision.

Typical fit:

- query surfaces: map discovered application-visible queries, rank by measured impact, and verify safe query or index improvements. A safe local fix is not complete unless discovered high-impact query surfaces have ledger dispositions.
- schema health: inventory discovered tables, indexes, constraints, relationships, migrations, app-assumed schema invariants, and growth risks for performance or reliability impact.
- runtime work: inspect backend code paths beyond the database, such as serial awaits, repeated initialization, blocking I/O, large responses, serialization cost, caching, and unnecessary repeated work.
- ops hygiene: inspect connection pooling, timeouts, lock risk, migration safety, vacuum/analyze or bloat signals, slow-query visibility, observability, and alerting gaps.

### `$merge-review`

Runs a goal-backed current-branch merge-readiness loop. Invoke it as:

```text
/goal $merge-review
```

It keeps `tasks/merge-review-<branch-slug>.md` current, reviews `origin/main...HEAD`, fixes verified local `Disposition: fix` findings, validates, and starts a fresh rereview until no fixable findings remain or a real blocker is proven. Its merge-readiness pass includes bounded adversarial-prior checks: try to prove the strongest bug candidate, look for a smaller safe delta, then reject unsupported hostile findings with falsifying evidence. It does not push, create PRs, merge, clean branches, or run a whole-repo production audit.

### `$plan-refine`

Modifiers:

- `--max-rounds=<n>`: set the review loop round cap. The default and hard maximum are 8.
- `--preserve-refine-artifacts`: keep the temporary refinement log after success.

Request context:

- `plan-key=<plan-key>`: select the artifact set. Bare `$plan-refine` works only when exactly one complete set exists.

Runs a bounded iterative critique loop over legacy PRD/TDD/tasks-plan artifacts. It edits planning artifacts only; it does not implement code. Prefer `$deliver` for new execution plans.

### `$review-chain`

Modifiers:

- `--preserve-review-artifacts`: keep review logs instead of cleaning them after success.

Request context:

- Optional task ID: review the branch against that planned task when task artifacts exist.

Runs explicit branch or task-scoped review without starting a repo-wide sweep.

It includes bounded adversarial-prior checks, but remains report-first by default. During the review, it assumes a bug may exist and there may be a smaller safe delta. The checks require evidence, a verification pivot, or `no action` with falsifying evidence instead of inventing a finding.

### `$review-plan`

Modifiers:

- `--approval-gate`: run the same review loop read-only, write proposed plan fixes to `tasks/tmp/review-plan-<plan-key>.md`, and stop before editing the execution plan.

Request context:

- `plan-key=<plan-key>`: select the execution plan when more than one active `$deliver` plan exists.

Runs an adversarial first-principles council loop over one active `$deliver` execution plan. It is planning-only: it may edit `tasks/execution-plan-<plan-key>.md`, but it must not edit implementation code or start implementation. Use it after `$deliver` writes the plan and before saying `implement the doc`.

Use `$review-plan` when an active `$deliver` execution plan should get an adversarial first-principles council pass before implementation.

### `$skill-review`

Modifiers:

- `--preserve-review-artifacts`: keep scratch artifacts after the review completes.

Request context:

- `skill=<skill-name>`: review one changed skill instead of inferring from the diff.
- `scenario=<path-or-name>`: use a provided scenario prompt, artifact, or named local case.
- `baseline=<git-ref>`: compare against this baseline instead of the resolved merge base or `origin/main`.
- `candidate=<git-ref-or-worktree>`: compare against this candidate instead of the current checkout.

Reviews Prime Directive skill changes before merge by comparing behavior on a realistic scenario. It extracts the baseline and candidate skill contracts, runs both versions with comparable inputs, preserves the run artifacts in a state doc and scratch directory, and uses a fresh judge to decide whether the candidate is better, neutral, regressive, or inconclusive.

### `$create-architecture`

Creates or updates a repo-specific `docs/ARCHITECTURE.md`. It records actual module boundaries, dependency direction, composition roots, shared-code rules, testing boundaries, architecture checks, and accepted deviations. Use it for non-trivial repos, greenfield architecture baselines, or before boundary-affecting work when no architecture doc exists.

### `$bootstrap-repo-rules`

Modifiers:

- `--with-hooks`: also wire local hooks when appropriate.

Sets up a repo's first meaningful validation surface: lint, format, typecheck, test, build, CI, and optionally local hooks. It detects the actual stack instead of forcing one preset.

### `$cleanup-merged-branches`

Safely deletes merged feature branches locally and on `origin` after checking the base branch, merge ancestry, and open PR state. Add a branch name when you want to inspect and clean only that branch instead of scanning all safe merged candidates.

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `setup` host-aware installer for Codex, Claude, and optional team auto-update
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer
- `scripts/install-claude-skills.sh` idempotent Claude skills installer
- `scripts/prime-directive-team-init.sh` repo-level AGENTS.md/CLAUDE.md bootstrapper
- `scripts/validate-skill-contracts.py` skill metadata and contract ownership validator

## Team Mode

Team mode keeps the global Prime Directive checkout as the source of truth and adds small repo-level instructions so teammates install the same skills without vendoring a `skills/` tree.

From inside a target repo:

```bash
(cd "$HOME/.prime-directive/repo" && ./setup --host auto --team) && "$HOME/.prime-directive/repo/scripts/prime-directive-team-init.sh" required
```

Use `optional` instead of `required` if you want the repo to suggest Prime Directive without blocking Claude skill usage.

What it does:

- `./setup --team` enables a Claude SessionStart hook that silently runs a throttled `git pull --ff-only` and reinstall for this Prime Directive checkout
- for Codex, `./setup --team` adds a managed block to `~/.codex/AGENTS.md` that tells Codex to run `scripts/prime-directive-codex-preflight.sh` before first Prime Directive skill use in a session
- `scripts/prime-directive-team-init.sh required` adds AGENTS.md and CLAUDE.md install checks to the target repo
- required mode also adds a Claude project PreToolUse hook that blocks skill usage when Prime Directive is missing
- Codex does not currently expose the same documented session-start hook surface as Claude, so the Codex hook is instruction-driven rather than a runtime callback

## Skill Authoring

Each skill lives in `skills/<skill-name>/SKILL.md`.

Conventions:

- keep the front matter `name` stable; that is the public identifier
- keep `description` concise and invocation-oriented
- use `skills/...` paths for internal references
- keep shared non-invokable references under `skills/shared/`
- keep reusable workflow contracts owned in one place; see `skills/shared/references/contract-ownership.md`

Keep the skill quick-reference table current when adding, renaming, or removing skills.

## Verification

Useful local checks:

```bash
python3 scripts/validate-skill-contracts.py
./setup --host auto
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./setup --host auto --team
HOME="$(mktemp -d)" ./setup --host auto --team
HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh
HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh
```

The contract validator checks public skill rows, modifier/request-option drift, owner-path rows, and known stale mirrors. The installers are expected to be idempotent.

## Optional ChatGPT Pro Analysis

Prime Directive can use a visible ChatGPT Pro browser pass as an internal escalation path for:

- `$first-principles-mode --pro-analysis`
- `$deliver --pro-analysis`
- `$deliver --deep-research --pro-analysis`
- `$repo-sweep --pro-analysis`

The public workflow stays on those skill modifiers. The implementation detail is direct browser control of the user's already-authenticated ChatGPT session: use the Chrome plugin/control surface against the user's normal Chrome profile first, and fall back to Computer Use when the visible UI is easier to operate than DOM selectors. Do not use the in-app Browser plugin, standalone Playwright tabs, or a newly launched browser profile as the Pro path.

If the visible browser target starts on `about:blank`, an empty new tab, or another non-ChatGPT page, the Pro workflow should first navigate it to `https://chat.com/`, then fall back to `https://chatgpt.com/` if needed, before declaring the browser path unavailable.

The Pro pass is not complete until the answer is read and reduced into `tasks/tmp/pro-analysis-<plan-key>.md` with browser evidence, a findings ledger, artifact deltas, and a completion stamp containing `pro_result_read: yes`, `pro_browser_run: yes`, `pro_model_selected: yes`, and `pro_synthesis_complete: yes`. The visible selected model must be `Pro Extended` or `Extended Pro`; `Thinking Extended` is not enough. If the browser cannot select the model, submit the bundle, wait for completion, or capture the answer, treat the Pro gate as failed rather than silently continuing.
