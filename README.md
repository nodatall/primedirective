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
| `bootstrap-repo-rules` | `$bootstrap-repo-rules` | `--with-hooks` |
| `cleanup-merged-branches` | `$cleanup-merged-branches` | Optional branch name in the request |
| `create-architecture` | `$create-architecture` | None |
| `deep-research-prompt` | `$deep-research-prompt` | None |
| `deliver` | `$deliver`, `$deliver refine`, or `$deliver plan` | `--pro-analysis`; legacy `$deliver discuss` is a draft-update alias |
| `fix-loop` | `$fix-loop <broken behavior>` | None |
| `first-principles-mode` | `$first-principles-mode` | `--deep-research`, `--pro-analysis` |
| `merge-review` | `$merge-review` inside /goal $merge-review | None |
| `plain-language` | `$plain-language` | None |
| `plan-refine` | `$plan-refine [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--max-rounds=<n>`, `--preserve-refine-artifacts`; max rounds default to 8 and are capped at 8 |
| `plan-to-goal` | `$plan-to-goal [plan-key=<plan-key>]` | `plan-key=<plan-key>` or source material in the thread |
| `repo-sweep` | `$repo-sweep` | `--pro-analysis`, `--swarm`, `--dep-scan`, `--preserve-review-artifacts`; `--swarm` includes nitpick depth; use `/goal $repo-sweep` for repair/resweep |
| `review-chain` | `$review-chain` | `--preserve-review-artifacts`; optional task ID in the request for task-scoped review |
| `ship-branch` | `$ship-branch` | None |

## Which Skill Do I Use?

- Use `$fix-loop` when one concrete thing is broken and you want Codex to reproduce, patch, retry the actual failing flow, add a focused probe when evidence is missing, and keep going until it is verified fixed or blocked.
- Use `$deep-research-prompt` when you want a paste-ready ChatGPT.com Deep Research prompt from the current thread before local planning or execution.
- Use `$deliver` when you want one readable execution plan refined right away, or a goal-plan prompt for adaptive evidence loops.
- Use `$deliver discuss` only when you want a draft checklist to stay current while you talk through it.
- Use `$deliver refine` or say `refine it` when an existing draft checklist is ready to become a reviewed execution plan; implementation still waits for approval.
- Use `$plan-to-goal` when a thread plan, readable execution plan, or PRD/TDD/tasks-plan set should become a reviewable goal-plan doc plus a separate compact paste-ready `/goal` prompt.
- Use `$plan-refine` only for legacy PRD/TDD/tasks-plan artifacts that need pressure testing before being converted into `$deliver` or a goal.
- Use `$review-chain` when you want a branch or task reviewed without a repo-wide sweep.
- Use `$merge-review` inside `/goal $merge-review` when the current branch should be made merge-ready through a review/fix/validate/rereview loop.
- Use `$repo-sweep` when you want a broad repository audit and production-readiness pass; use `/goal $repo-sweep` when you want the repair/resweep loop. Use `/goal $repo-sweep --swarm --preserve-review-artifacts` when you want a longer nitpicky sweep for maintainability, test quality, code slop, and production risk.
- Use `$first-principles-mode` when the main need is deep read-only analysis, not edits; if current evidence cannot separate the leading explanations, it should name the smallest verification step instead of giving a polished guess.
- Use `$bootstrap-repo-rules` when a repo needs its first meaningful validation, formatting, build, test, or CI surface.
- Use `$cleanup-merged-branches` when you want safe local and remote cleanup of merged branches.
- Use `$create-architecture` when a non-trivial repo needs a concrete `docs/ARCHITECTURE.md`, or before boundary-affecting work when that file is missing.
- Use `$plain-language` when you want a shorter, clearer, plainer answer or rewrite.
- Use `$ship-branch` when the current feature branch should be pushed, PR'd, merged, deleted locally/remotely, and the checkout returned to the base branch.

## Skill Details

### `$bootstrap-repo-rules`

Sets up a repo's first meaningful validation surface: lint, format, typecheck, test, build, CI, and optionally local hooks. It detects the actual stack instead of forcing one preset.

Modifiers:

- `--with-hooks`: also wire local hooks when appropriate.

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

Modifiers:

- None.

### `$deliver`

Creates or loads one plain-language execution plan, runs ChatGPT Pro pressure when requested, refines the plan immediately, asks the user to review the Markdown plan file, or delegates to `$plan-to-goal` when the source is really an adaptive evidence loop. Draft checklist mode remains available through legacy `$deliver discuss` for explicit planning discussion. After refinement and user approval, the plan is checked until no material backlog issues remain, then worked through one unchecked item at a time with focused validation, useful commits, plan updates, final review, and a pre-handoff unchecked-box gate.

Request options:

- bare `$deliver`, `refine`, or `plan`: keep the active checklist in `tasks/execution-plan-<plan-key>.md`, replace any draft instruction with the Deliver implementation instruction, refine it, and ask the user to review the Markdown file before approving implementation.
- `discuss`: legacy alias for creating or updating the same draft checklist plan. Do not treat it as a separate workflow.

Modifiers:

- `--pro-analysis`: run ChatGPT Pro browser escalation after the readable execution plan exists, synthesize findings into the plan, then refine and ask the user to review the Markdown file only after the Pro synthesis gate succeeds.

### `$plan-to-goal`

Converts messy source material, a readable execution plan, or PRD/TDD/tasks-plan artifacts into `tasks/goal-plan-<plan-key>.md`, then prints a separate compact paste-ready `/goal` prompt that references that file. The goal plan includes target/baseline guidance when metrics exist, state-recording guidance for long runs, and review wording that asks the user to say `start this as a goal`.

Request options:

- `plan-key=<plan-key>`: build the goal plan from an existing PRD/TDD/tasks-plan set.
- Source material in the thread: build the goal plan from the current conversation or pasted plan.

Modifiers:

- None.

### `$fix-loop`

Targets one concrete broken behavior. It reproduces the failure, patches the root cause, reruns the actual failing flow, reads fresh evidence, and repeats until the behavior is verified fixed or blocked. If repeated patches would be guesses, it adds the smallest useful log, deterministic test, replay, behavior probe, or harness before another fix attempt.

Request options:

- `<broken behavior>`: a short natural-language bug report, such as `checkout is 500ing locally` or `settings page flashes blank on launch`.

Modifiers:

- None.

### `$first-principles-mode`

Runs a deep, read-only analysis pass. It is for mechanism-level judgment, competing explanations, root-cause reasoning, or plan critique before deciding what to build or change. It uses a default adversarial council with independent lanes and rebuttal rounds before synthesis. When the evidence cannot separate plausible explanations, it should stop and name the smallest verification step needed next.

Modifiers:

- `--deep-research`: add web-backed operator/current-practice research with an evidence bar.
- `--pro-analysis`: escalate through the ChatGPT Pro browser wrapper and synthesize the result back into the local analysis.

### `$merge-review`

Runs a goal-backed current-branch merge-readiness loop. Invoke it as:

```text
/goal $merge-review
```

It keeps `tasks/merge-review-<branch-slug>.md` current, reviews `origin/main...HEAD`, fixes verified local `Disposition: fix` findings, validates, and starts a fresh rereview until no fixable findings remain or a real blocker is proven. It does not push, create PRs, merge, clean branches, or run a whole-repo production audit.

Modifiers:

- None.

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

Request options:

- Optional task ID: review the branch against that planned task when task artifacts exist.

Modifiers:

- `--preserve-review-artifacts`: keep review logs instead of cleaning them after success.

### `$ship-branch`

Finishes the current feature branch. It handles dirty work first by showing a compact status/diff summary and asking whether to commit or stash, then pushes the branch, creates or reuses a PR, merges it, deletes the remote branch, switches back to the base branch, pulls the merged base, and deletes the local branch.

Modifiers:

- None.

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer
- `scripts/install-claude-skills.sh` idempotent Claude skills installer
- `scripts/validate-skill-contracts.py` skill metadata and contract ownership validator

## Install For Codex

Run from this repository root:

```bash
./scripts/install-codex-plugin.sh
```

What it does:

- creates `~/.agents/plugins/marketplace.json` when missing
- adds or updates one local `prime-directive` plugin entry that points at this checkout
- enables `prime-directive@local-marketplace` in `~/.codex/config.toml`
- symlinks each repo skill into `~/.codex/skills/` for Codex builds that read local skills directly
- preserves other marketplace entries

Update flow:

1. Pull the latest changes in this repo.
2. Re-run `./scripts/install-codex-plugin.sh` if you added, renamed, or removed skills.
3. Restart Codex if the updated skills do not appear immediately.

## Install For Claude

Run from this repository root:

```bash
./scripts/install-claude-skills.sh
```

What it does:

- creates `~/.claude/skills` when missing
- symlinks each repo skill into `~/.claude/skills/<skill-name>`
- skips existing non-symlink skill directories instead of overwriting them
- preserves other Claude config and plugin state

Set `CLAUDE_SKILLS_DIR=/custom/path` if your Claude setup expects a different global skills location.

Update flow:

1. Pull the latest changes in this repo.
2. Re-run `./scripts/install-claude-skills.sh`.
3. Restart Claude or open a fresh Claude session if the updated skills do not appear immediately.

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
./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh
HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh
```

The contract validator checks public skill rows, modifier/request-option drift, owner-path rows, and known stale mirrors. The installers are expected to be idempotent.

## Optional ChatGPT Pro Analysis

Prime Directive can use a visible ChatGPT Pro browser pass as an internal escalation path for:

- `$first-principles-mode --pro-analysis`
- `$deliver --pro-analysis`
- `$repo-sweep --pro-analysis`

The public workflow stays on those skill modifiers. The implementation detail is direct browser control of the user's already-authenticated ChatGPT session: use Chrome automation first, and fall back to Computer Use when the visible UI is easier to operate than DOM selectors.

The Pro pass is not complete until the answer is read and reduced into `tasks/tmp/pro-analysis-<plan-key>.md` with browser evidence, a findings ledger, artifact deltas, and a completion stamp containing `pro_result_read: yes`, `pro_browser_run: yes`, `pro_model_selected: yes`, and `pro_synthesis_complete: yes`. The visible selected model must be `Pro Extended` or `Extended Pro`; `Thinking Extended` is not enough. If the browser cannot select the model, submit the bundle, wait for completion, or capture the answer, treat the Pro gate as failed rather than silently continuing.
