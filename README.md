# Prime Directive

Prime Directive is a Codex plugin source repo that ships reusable workflow skills from a single canonical `skills/` tree.

The repo is Codex-first:

- install it globally as a local Codex plugin
- treat this checkout as the only source of truth for skill authoring

## Skill Quick Reference

All skills use explicit Codex-native `$skill-name` invocation text.

Use this table when you already know the skill name. The detailed sections below explain when to use each skill and what each modifier changes.

| Skill | Invocation | Modifiers and request options |
| --- | --- | --- |
| `backend-optimizer` | `$backend-optimizer` | None |
| `bootstrap-repo-rules` | `$bootstrap-repo-rules` | `--with-hooks` |
| `clarifier` | `$clarifier` | None |
| `cleanup-merged-branches` | `$cleanup-merged-branches` | Optional branch name in the request |
| `create-architecture` | `$create-architecture` | None |
| `deep-research-prompt` | `$deep-research-prompt` | None |
| `deliver` | `$deliver`, `$deliver refine`, or `$deliver plan` | `--deep-research`, `--pro-analysis`, `--fast`; legacy `$deliver discuss` is a draft-update alias |
| `first-principles-mode` | `$first-principles-mode` | `--deep-research`, `--pro-analysis` |
| `merge-review` | `$merge-review` inside /goal $merge-review | None |
| `page-speed-optimizer` | `$page-speed-optimizer` | None |
| `plain-language` | `$plain-language` | None |
| `plan-refine` | `$plan-refine [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--max-rounds=<n>`, `--preserve-refine-artifacts`; max rounds default to 8 and are capped at 8 |
| `plan-to-goal` | `$plan-to-goal [plan-key=<plan-key>]` | `plan-key=<plan-key>` or source material in the thread |
| `repo-sweep` | `$repo-sweep` | `--pro-analysis`, `--swarm`, `--dep-scan`, `--preserve-review-artifacts`; `--swarm` includes nitpick depth; use `/goal $repo-sweep` for repair/resweep |
| `review-chain` | `$review-chain` | `--preserve-review-artifacts`; optional task ID in the request for task-scoped review |
| `review-plan` | `$review-plan [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--approval-gate`; reviews active `$deliver` execution plans |
| `skill-review` | `$skill-review [skill=<skill-name>]` | `skill=<skill-name>`, `scenario=<path-or-name>`, `baseline=<git-ref>`, `candidate=<git-ref-or-worktree>`, `--preserve-review-artifacts` |
| `ship-branch` | `$ship-branch` | None |

## Which Skill Do I Use?

- Use `$clarifier` when you want help turning a rough draft or stuck thought into clearer writing by revising it yourself with questions and short teaching examples.
- Use `$deep-research-prompt` when you want a paste-ready ChatGPT.com Deep Research prompt from the current thread before local planning or execution.
- Use `$deliver` when you want one readable execution plan refined right away, or a goal-plan prompt for adaptive evidence loops.
- Use `$backend-optimizer` when the work is specifically backend or database performance: exhaustive query sweeps, schema/index health, backend runtime cost, or operational database hygiene. Bare `$backend-optimizer` is report-first; use `/goal $backend-optimizer` for the bounded measured fix loop.
- Use `$deliver discuss` only when you want a draft checklist to stay current while you talk through it.
- Use `$deliver refine` or say `refine it` when an existing draft checklist is ready to become a reviewed execution plan; implementation still waits for approval unless `--fast` is present.
- Use `$plan-to-goal` when a rough goal prompt, thread plan, readable execution plan, or PRD/TDD/tasks-plan set should become a reviewable goal-plan doc with an embedded copy-pasteable `/goal` start prompt.
- Use `$plan-refine` only for legacy PRD/TDD/tasks-plan artifacts that need pressure testing before being converted into `$deliver` or a goal.
- Use `$review-plan` when an active `$deliver` execution plan should get an adversarial first-principles council pass before implementation. It patches the plan by default and stops before code changes.
- Use `$review-chain` when you want a branch or task reviewed without a repo-wide sweep. It includes bounded adversarial-prior checks, but remains report-first by default.
- Use `$merge-review` inside `/goal $merge-review` when the current branch should be made merge-ready through a review/fix/validate/rereview loop. It uses the same bounded adversarial-prior checks before declaring the branch ready.
- Use `$page-speed-optimizer` when the work is specifically frontend journey speed: page load, Core Web Vitals, interaction responsiveness, route transitions, flashes, layout shifts, bfcache/back-forward behavior, frontend assets, third-party cost, or browser-perceived performance. Bare `$page-speed-optimizer` is report-first; use `/goal $page-speed-optimizer` for the bounded measured fix loop.
- Use `$skill-review` before merging Prime Directive skill changes when you want evidence that the candidate skill contract works better in practice. It runs baseline and candidate skill versions against the same realistic scenario, then judges the artifacts.
- Use `$repo-sweep` when you want a broad repository audit and production-readiness pass; use `/goal $repo-sweep` when you want the repair/resweep loop. Use `/goal $repo-sweep --swarm --preserve-review-artifacts` when you want a longer nitpicky sweep for maintainability, test quality, code slop, and production risk.
- Use `$first-principles-mode` when the main need is deep read-only analysis, not edits; if current evidence cannot separate the leading explanations, it should name the smallest verification step instead of giving a polished guess.
- Use `$bootstrap-repo-rules` when a repo needs its first meaningful validation, formatting, build, test, or CI surface.
- Use `$cleanup-merged-branches` when you want safe local and remote cleanup of merged branches.
- Use `$create-architecture` when a non-trivial repo needs a concrete `docs/ARCHITECTURE.md`, or before boundary-affecting work when that file is missing.
- Use `$plain-language` when you want a shorter, clearer, plainer answer or rewrite.
- Use `$ship-branch` when the current feature branch should be pushed, PR'd, merged, deleted locally/remotely, and the checkout returned to the base branch.

## Skill Details

### `$backend-optimizer`

Improves backend and database performance with measured evidence. It is narrower than `$repo-sweep`: use it for query performance, schema/index health, backend runtime cost, and operational database hygiene, not for broad security, architecture redesign, frontend performance, dependency audit, or whole-repo production-readiness review.

Bare `$backend-optimizer` is report-first: it inventories, ranks, measures where practical, and recommends fixes before stopping for approval. Invoke `/goal $backend-optimizer` when safe measured fixes should proceed in a bounded loop until every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision.

No public mode flags are required. `/goal $backend-optimizer` is enough; the skill carries the query, schema, runtime, ops-hygiene, goal-state, ledger, safety, and completion-gate instructions.

Typical fit:

- query surfaces: map discovered application-visible queries, rank by measured impact, and verify safe query or index improvements. A safe local fix is not complete unless discovered high-impact query surfaces have ledger dispositions.
- schema health: inventory discovered tables, indexes, constraints, relationships, migrations, app-assumed schema invariants, and growth risks for performance or reliability impact.
- runtime work: inspect backend code paths beyond the database, such as serial awaits, repeated initialization, blocking I/O, large responses, serialization cost, caching, and unnecessary repeated work.
- ops hygiene: inspect connection pooling, timeouts, lock risk, migration safety, vacuum/analyze or bloat signals, slow-query visibility, observability, and alerting gaps.

### `$bootstrap-repo-rules`

Sets up a repo's first meaningful validation surface: lint, format, typecheck, test, build, CI, and optionally local hooks. It detects the actual stack instead of forcing one preset.

Modifiers:

- `--with-hooks`: also wire local hooks when appropriate.

### `$clarifier`

Coaches revision for rough drafts, stuck thoughts, posts, essays, messages, and explanations. It restates the intended meaning, identifies one clarity issue, asks focused questions, may show one short annotated teaching example, and asks the user to write the next version themselves.

Modifiers:

- None.

### `$cleanup-merged-branches`

Safely deletes merged feature branches locally and on `origin` after checking the base branch, merge ancestry, and open PR state.

Request options:

- Optional branch name: inspect and clean only that branch instead of scanning all safe merged candidates.

### `$create-architecture`

Creates or updates a repo-specific `docs/ARCHITECTURE.md`. It records actual module boundaries, dependency direction, composition roots, shared-code rules, testing boundaries, architecture checks, and accepted deviations. Use it for non-trivial repos, greenfield architecture baselines, or before boundary-affecting work when no architecture doc exists.

Modifiers:

- None.

### `$deep-research-prompt`

Creates a paste-ready prompt for ChatGPT.com Deep Research from the current thread. It assumes you will manually select the relevant GitHub repo, files, or project context in ChatGPT before starting the research.

The generated prompt asks Deep Research to end with a load-bearing falsification pass: test the claims that would change the recommendation if wrong, search for counterevidence when needed, and revise the conclusion when the evidence breaks.

Modifiers:

- None.

### `$deliver`

Creates or loads one plain-language execution plan, runs web-backed deep research when requested, runs ChatGPT Pro pressure when requested, refines the plan immediately, asks the user to review the Markdown plan file unless `--fast` is present, or delegates to `$plan-to-goal` when the source is really an adaptive evidence loop. For frontend-facing plans, it creates a simple linked HTML mockup before approval so the user can see the expected visual direction. Draft checklist mode remains available through legacy `$deliver discuss` for explicit planning discussion. After refinement and user approval, or immediately after refinement in `--fast` mode, the plan is checked until no material backlog issues remain, then worked through one unchecked item at a time with focused validation, useful commits, plan updates, final review, and a pre-handoff unchecked-box gate.

Request options:

- bare `$deliver`, `refine`, or `plan`: keep the active checklist in `tasks/execution-plan-<plan-key>.md`, replace any draft instruction with the Deliver implementation instruction, refine it, and ask the user to review the Markdown file before approving implementation unless `--fast` is present.
- `discuss`: legacy alias for creating or updating the same draft checklist plan. Do not treat it as a separate workflow.

Modifiers:

- `--deep-research`: run web-backed operator/current-practice research after the readable execution plan exists, synthesize adopted findings into the plan, then continue to Pro analysis when requested or refinement when not.
- `--pro-analysis`: run ChatGPT Pro browser escalation after the readable execution plan exists, synthesize findings into the plan, then refine and ask the user to review the Markdown file only after the Pro synthesis gate succeeds.
- `--deep-research --pro-analysis`: run deep research first, apply adopted findings to the execution plan, then run ChatGPT Pro against the researched plan before refinement.
- `--fast`: skip only the initial plan-review pause after refinement, then start implementation immediately; validation, final review, archive, commit, and finalization still run.

### `$plan-to-goal`

Converts messy source material, rough goal prompts, readable execution plans, or PRD/TDD/tasks-plan artifacts into `tasks/goal-plan-<plan-key>.md`, with an embedded copy-pasteable `/goal` start prompt that references that file. Before writing the file, it optimizes rough prose into a first-screen `Goal`, `Done When`, `Not Done Yet If`, and `Start Prompt` block, then fills in the plain-language summary, starting evidence, target/baseline, work loop, primary verifier, supporting checks, measurable acceptance criteria, anti-cheat criteria, explicit stop conditions, boundaries, and resume state. The goal plan includes target/baseline guidance when metrics exist, finish-line-first review guidance, state-recording guidance for long runs, and no-early-stop guidance.

Request options:

- `plan-key=<plan-key>`: build the goal plan from an existing PRD/TDD/tasks-plan set.
- Source material in the thread: build the goal plan from the current conversation, rough goal prompt, diagnosis, recommendation text, or pasted plan.

Modifiers:

- None.

### `$first-principles-mode`

Runs a deep, read-only analysis pass. It is for mechanism-level judgment, competing explanations, root-cause reasoning, or plan critique before deciding what to build or change. It uses a default adversarial council with independent lanes and rebuttal rounds before synthesis. It gives extra falsification effort to load-bearing claims that would change the conclusion, confidence, or next verification step if wrong. When the evidence cannot separate plausible explanations, it should stop and name the smallest verification step needed next.

Modifiers:

- `--deep-research`: add web-backed operator/current-practice research with an evidence bar.
- `--pro-analysis`: escalate through the ChatGPT Pro browser wrapper and synthesize the result back into the local analysis.

### `$merge-review`

Runs a goal-backed current-branch merge-readiness loop. Invoke it as:

```text
/goal $merge-review
```

It keeps `tasks/merge-review-<branch-slug>.md` current, reviews `origin/main...HEAD`, fixes verified local `Disposition: fix` findings, validates, and starts a fresh rereview until no fixable findings remain or a real blocker is proven. Its merge-readiness pass includes bounded adversarial-prior checks: try to prove the strongest bug candidate, look for a smaller safe delta, then reject unsupported hostile findings with falsifying evidence. It does not push, create PRs, merge, clean branches, or run a whole-repo production audit.

Modifiers:

- None.

### `$page-speed-optimizer`

Improves real user-perceived frontend journey speed and visual continuity with measured evidence. It is narrower than `$repo-sweep`: use it for page loads, in-session navigation, interaction responsiveness, Core Web Vitals, visual transition quality, frontend assets, third-party scripts, bfcache behavior, and deployed browser-performance surfaces, not for backend query optimization or broad production-readiness review.

Bare `$page-speed-optimizer` is report-first: it inventories journeys, ranks candidates, measures where practical, and recommends fixes before stopping for approval. Invoke `/goal $page-speed-optimizer` when safe measured fixes should proceed in a bounded loop until every high-impact page, transition, interaction, asset, third-party, or deploy/cache candidate is improved, rejected with evidence, or gated behind a clear decision.

There are no public mode flags. `/goal $page-speed-optimizer` is enough; the skill carries the journey inventory, goal-run state document, ledger expectations, safety rules, measurement requirements, and completion gate.

### `$plain-language`

Produces a shorter, clearer, more direct explanation or rewrite.

Modifiers:

- None.

### `$plan-refine`

Runs a bounded iterative critique loop over legacy PRD/TDD/tasks-plan artifacts. It edits planning artifacts only; it does not implement code. Prefer `$deliver` for new execution plans.

Request options:

- `plan-key=<plan-key>`: select the artifact set. Bare `$plan-refine` works only when exactly one complete set exists.

Modifiers:

- `--max-rounds=<n>`: set the review loop round cap. The default and hard maximum are 8.
- `--preserve-refine-artifacts`: keep the temporary refinement log after success.

### `$repo-sweep`

Runs a broad repository audit. It starts with first-principles no-edit analysis, runs review/security/production-readiness checks, reports findings, and pauses before fixes. Invoke `/goal $repo-sweep` for the bounded repair/resweep loop.

Modifiers:

- `--pro-analysis`: use ChatGPT Pro browser escalation as Round 1 audit-thesis input.
- `--swarm`: add parallel read-only discovery lanes for intent/regression, security/privacy, performance/reliability, contracts/coverage, and nitpick-depth maintainability/code-quality review before the report.
- `--dep-scan`: run an explicit dependency and supply-chain audit, reporting unavailable scanners as residual risk.
- `--preserve-review-artifacts`: keep sweep/review logs instead of cleaning them after success.

### `$review-chain`

Runs explicit branch or task-scoped review without starting a repo-wide sweep.

It runs bounded adversarial-prior checks during the review: assume a bug may exist, assume there may be a smaller safe delta, and then require evidence, a verification pivot, or `no action` with falsifying evidence instead of inventing a finding.

Request options:

- Optional task ID: review the branch against that planned task when task artifacts exist.

Modifiers:

- `--preserve-review-artifacts`: keep review logs instead of cleaning them after success.

### `$review-plan`

Runs an adversarial first-principles council loop over one active `$deliver` execution plan. It is planning-only: it may edit `tasks/execution-plan-<plan-key>.md`, but it must not edit implementation code or start implementation. Use it after `$deliver` writes the plan and before saying `implement the doc`.

Request options:

- `plan-key=<plan-key>`: select the execution plan when more than one active `$deliver` plan exists.

Modifiers:

- `--approval-gate`: run the same review loop read-only, write proposed plan fixes to `tasks/tmp/review-plan-<plan-key>.md`, and stop before editing the execution plan.

### `$skill-review`

Reviews Prime Directive skill changes before merge by comparing behavior on a realistic scenario. It extracts the baseline and candidate skill contracts, runs both versions with comparable inputs, preserves the run artifacts in a state doc and scratch directory, and uses a fresh judge to decide whether the candidate is better, neutral, regressive, or inconclusive.

Request options:

- `skill=<skill-name>`: review one changed skill instead of inferring from the diff.
- `scenario=<path-or-name>`: use a provided scenario prompt, artifact, or named local case.
- `baseline=<git-ref>`: compare against this baseline instead of the resolved merge base or `origin/main`.
- `candidate=<git-ref-or-worktree>`: compare against this candidate instead of the current checkout.

Modifiers:

- `--preserve-review-artifacts`: keep scratch artifacts after the review completes.

### `$ship-branch`

Finishes the current feature branch. It handles dirty work first by showing a compact status/diff summary and asking whether to commit or stash, then pushes the branch, creates or reuses a PR, waits for pending or queued required checks, fixes actionable check failures with focused commits, merges the PR, deletes the remote branch, switches back to the base branch, pulls the merged base, and deletes the local branch.

Modifiers:

- None.

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `setup` host-aware installer for Codex, Claude, and optional team auto-update
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer
- `scripts/install-claude-skills.sh` idempotent Claude skills installer
- `scripts/prime-directive-team-init.sh` repo-level AGENTS.md/CLAUDE.md bootstrapper
- `scripts/validate-skill-contracts.py` skill metadata and contract ownership validator

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

## Install For Codex

Run from this repository root:

```bash
./setup --host codex
```

What it does:

- creates `~/.agents/plugins/marketplace.json` when missing
- adds or updates one local `prime-directive` plugin entry that points at this checkout
- enables `prime-directive@local-marketplace` in `~/.codex/config.toml`
- symlinks each repo skill into `~/.codex/skills/` for Codex builds that read local skills directly
- preserves other marketplace entries

Update flow:

1. Pull the latest changes in this repo.
2. Re-run `./setup --host codex` if you added, renamed, or removed skills.
3. Restart Codex if the updated skills do not appear immediately.

## Install For Claude

Run from this repository root:

```bash
./setup --host claude
```

What it does:

- creates `~/.claude/skills` when missing
- symlinks each repo skill into `~/.claude/skills/<skill-name>`
- skips existing non-symlink skill directories instead of overwriting them
- preserves other Claude config and plugin state

Set `CLAUDE_SKILLS_DIR=/custom/path` if your Claude setup expects a different global skills location.

Update flow:

1. Pull the latest changes in this repo.
2. Re-run `./setup --host claude`.
3. Restart Claude or open a fresh Claude session if the updated skills do not appear immediately.

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

Codex invocation is explicit; keep the complete list in `Skill Invocations` current when adding, renaming, or removing skills.

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
