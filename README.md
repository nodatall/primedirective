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
| `deep-research-prompt` | `$deep-research-prompt` | None |
| `deliver` | `$deliver` | None |
| `execute-task` | `$execute-task task-id=<task-id> [plan-key=<plan-key>]` or `$execute-task --one-shot [plan-key=<plan-key>]` | `--one-shot`, `--stay-on-current-branch`, `--check-harness-drift`, `--preserve-review-artifacts`; `plan-key=<plan-key>` when it cannot be inferred |
| `fix-loop` | `$fix-loop <broken behavior>` | None |
| `first-principles-mode` | `$first-principles-mode` | `--deep-research`, `--pro-analysis` |
| `plain-language` | `$plain-language` | None |
| `plan-and-execute` | `$plan-and-execute` | `--prepare-plan`, `--deep-research`, `--pro-analysis`, `--refine-plan`, `--check-harness-drift`, `--preserve-artifacts` |
| `plan-refine` | `$plan-refine [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--max-rounds=<n>`, `--preserve-refine-artifacts`; max rounds default to 8 and are capped at 8 |
| `plan-to-goal` | `$plan-to-goal [plan-key=<plan-key>]` | `plan-key=<plan-key>` or source material in the thread |
| `plan-work` | `$plan-work` | `--from-thread`, `--direct`, `--grill`, `--deep-research`, `--preserve-planning-artifacts` |
| `repo-sweep` | `$repo-sweep` | `--pro-analysis`, `--loop`, `--swarm`, `--dep-scan`, `--preserve-review-artifacts` |
| `review-chain` | `$review-chain` | `--preserve-review-artifacts`; optional task ID in the request for task-scoped review |

## Which Skill Do I Use?

- Use `$fix-loop` when one concrete thing is broken and you want Codex to reproduce, patch, retry the actual failing flow, add a focused probe when evidence is missing, and keep going until it is verified fixed or blocked.
- Use `$deep-research-prompt` when you want a paste-ready ChatGPT.com Deep Research prompt from the current thread before local planning or execution.
- Use `$deliver` when you want one readable execution plan, or a goal-plan prompt for adaptive evidence loops, with refinement and user approval before execution starts.
- Use `$plan-work` when you want PRD/TDD/tasks-plan artifacts but do not want implementation yet.
- Use `$plan-and-execute` when the thread already has enough direction and you want planning plus execution in one run.
- Use `$plan-and-execute --prepare-plan` when a plan was discussed in the thread and you want Codex to restate it plainly before the one-shot run starts.
- Use `$plan-to-goal` when a thread plan, readable execution plan, or PRD/TDD/tasks-plan set should become a reviewable goal-plan doc with a compact paste-ready `/goal` prompt.
- Use `$execute-task` when planning artifacts already exist and you want one task, or all remaining tasks with `--one-shot`, implemented.
- Use `$plan-refine` when planning artifacts exist but need pressure testing before execution.
- Use `$review-chain` when you want a branch or task reviewed without a repo-wide sweep.
- Use `$repo-sweep` when you want a broad repository audit, production-readiness pass, and optional repair loop.
- Use `$first-principles-mode` when the main need is deep read-only analysis, not edits; if current evidence cannot separate the leading explanations, it should name the smallest verification step instead of giving a polished guess.
- Use `$bootstrap-repo-rules` when a repo needs its first meaningful validation, formatting, build, test, or CI surface.
- Use `$cleanup-merged-branches` when you want safe local and remote cleanup of merged branches.
- Use `$plain-language` when you want a shorter, clearer, plainer answer or rewrite.

## Skill Details

### `$bootstrap-repo-rules`

Sets up a repo's first meaningful validation surface: lint, format, typecheck, test, build, CI, and optionally local hooks. It detects the actual stack instead of forcing one preset.

Modifiers:

- `--with-hooks`: also wire local hooks when appropriate.

### `$cleanup-merged-branches`

Safely deletes merged feature branches locally and on `origin` after checking the base branch, merge ancestry, and open PR state.

Request options:

- Optional branch name: inspect and clean only that branch instead of scanning all safe merged candidates.

### `$deep-research-prompt`

Creates a paste-ready prompt for ChatGPT.com Deep Research from the current thread. It assumes you will manually select the relevant GitHub repo, files, or project context in ChatGPT before starting the research.

Modifiers:

- None.

### `$deliver`

Creates or loads one plain-language execution plan, or delegates to `$plan-to-goal` when the source is really an adaptive evidence loop. Normal execution plans are refined until no material backlog issues remain, approved by the user, then worked through one unchecked item at a time with focused validation, useful commits, plan updates, final review, and a pre-handoff unchecked-box gate.

Modifiers:

- None.

### `$execute-task`

Implements work from existing `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, and `tasks/tasks-plan-<plan-key>.md` artifacts.

Request options:

- `task-id=<task-id>`: run one planned task in standard mode.
- `plan-key=<plan-key>`: select the artifact set when it cannot be inferred.

Modifiers:

- `--one-shot`: execute all remaining unchecked tasks in order, then run final review/finalization.
- `--stay-on-current-branch`: do not create or switch branches before execution.
- `--check-harness-drift`: include a compact check for whether execution drifted from the harness/plan contract.
- `--preserve-review-artifacts`: keep temporary review artifacts instead of cleaning them after success.

### `$plan-to-goal`

Converts messy source material, a readable execution plan, or PRD/TDD/tasks-plan artifacts into `tasks/goal-plan-<plan-key>.md`. The goal plan includes a compact paste-ready `/goal` prompt, target/baseline guidance when metrics exist, state-recording guidance for long runs, and review wording that asks the user to say `start this as a goal`.

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

### `$plain-language`

Produces a shorter, clearer, more direct explanation or rewrite.

Modifiers:

- None.

### `$plan-and-execute`

Turns the current thread plan into PRD/TDD/tasks-plan artifacts, then executes the work end to end. It is the one-command path when you want planning and implementation together.

Modifiers:

- `--deep-research`: strengthen planning with web-backed research before task generation and execution.
- `--pro-analysis`: run ChatGPT Pro browser escalation during planning, then continue only after local synthesis succeeds.
- `--prepare-plan`: restate the full current plan in plain English, continue if the user confirms it, or ask up to five non-obvious plain-English questions before summarizing and waiting for confirmation.
- `--refine-plan`: run `$plan-refine` before execution.
- `--check-harness-drift`: include a compact drift check in the final handoff.
- `--preserve-artifacts`: keep planning, review, or temporary artifacts that would normally be cleaned up.

### `$plan-refine`

Runs a bounded iterative critique loop over existing PRD/TDD/tasks-plan artifacts. It edits planning artifacts only; it does not implement code.

Request options:

- `plan-key=<plan-key>`: select the artifact set. Bare `$plan-refine` works only when exactly one complete set exists.

Modifiers:

- `--max-rounds=<n>`: set the review loop round cap. The default and hard maximum are 8.
- `--preserve-refine-artifacts`: keep the temporary refinement log after success.

### `$plan-work`

Creates PRD/TDD/tasks-plan artifacts from a request, source plan, or current thread. It is planning only.

Modifiers:

- `--from-thread`: treat the conversation above the trigger as the source plan.
- `--direct`: avoid the normal planning-question flow and make reasonable assumptions.
- `--grill`: ask a tighter clarification sequence before writing artifacts.
- `--deep-research`: add web-backed research before finalizing the plan.
- `--preserve-planning-artifacts`: keep temporary planning artifacts that would normally be cleaned up.

### `$repo-sweep`

Runs a broad repository audit. It starts with first-principles no-edit analysis, runs review/security/production-readiness checks, reports findings, and can optionally proceed into a bounded repair/resweep loop.

Modifiers:

- `--pro-analysis`: use ChatGPT Pro browser escalation as Round 1 audit-thesis input.
- `--loop`: treat the invocation as approval to fix verified, in-scope findings and resweep until clean, blocked, or capped.
- `--swarm`: add parallel read-only discovery lanes for intent/regression, security/privacy, performance/reliability, and contracts/coverage before the report.
- `--dep-scan`: run an explicit dependency and supply-chain audit, reporting unavailable scanners as residual risk.
- `--preserve-review-artifacts`: keep sweep/review logs instead of cleaning them after success.

### `$review-chain`

Runs explicit branch or task-scoped review without starting a repo-wide sweep.

Request options:

- Optional task ID: review the branch against that planned task when task artifacts exist.

Modifiers:

- `--preserve-review-artifacts`: keep review logs instead of cleaning them after success.

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer
- `scripts/install-claude-skills.sh` idempotent Claude skills installer
- `scripts/oracle-pro.sh` ChatGPT Pro browser escalation wrapper for Prime Directive analysis flows
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

## Optional ChatGPT Pro Escalation

Prime Directive can use ChatGPT Pro browser mode as an internal escalation path for:

- `$first-principles-mode --pro-analysis`
- `$plan-and-execute --pro-analysis`
- `$repo-sweep --pro-analysis`

The public workflow stays on those skill modifiers. The implementation detail is the repo wrapper:

```bash
./scripts/oracle-pro.sh setup
./scripts/oracle-pro.sh session
./scripts/oracle-pro.sh dry-run -p "Analyze this repo" --file .
./scripts/oracle-pro.sh run -p "Analyze this repo" --file .
```

Run setup once when the browser profile needs ChatGPT login. If setup reports a duplicate running session, use `./scripts/oracle-pro.sh session` to reattach or `./scripts/oracle-pro.sh setup --force` to start a fresh setup check. The setup action skips model-picker and thinking-time UI selection because it is only a login/profile check. Normal dry-run/run/render actions now try to select the requested ChatGPT model by default so they do not inherit arbitrary browser state such as a leftover Thinking or Playwright mode, and they use extended thinking unless you override it. The default model request is the ChatGPT browser label `Extended Pro`; Oracle stores that as `gpt-5.5-pro`, but the wrapper avoids a separate best-effort thinking-time click on the default path so the UI is not first set to Extended Pro and then downgraded by a later control pass. The wrapper prints a safe invocation summary showing action, model, model strategy, and thinking mode; `--pro-analysis` planning gates require the real run to show extended thinking before the Pro synthesis can be marked complete. Set `ORACLE_PRO_MODEL_STRATEGY=current` only when you explicitly want to reuse the browser's current mode, `ORACLE_PRO_THINKING=heavy` only when that option exists, or `ORACLE_PRO_MODEL_STRATEGY=ignore ORACLE_PRO_THINKING=off` if ChatGPT hides or drifts the live controls and you want a fully UI-light fallback. That fallback is degraded mode, not a completed extended-thinking Pro pass. When `ORACLE_BIN` is unset, the wrapper uses `npx -y @steipete/oracle@0.10.0`; Oracle upstream now expects Node 24+. The wrapper owns Oracle defaults for browser mode, Pro model, manual-login profile reuse, file bundling, timeouts, dry-run previews, and local temp cleanup. Set `ORACLE_PRO_KEEP_TMP=1` to keep the wrapper temp directory for debugging.
