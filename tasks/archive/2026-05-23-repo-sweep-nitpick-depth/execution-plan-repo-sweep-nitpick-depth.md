# Repo Sweep Nitpick Depth
Goal: Make `$repo-sweep` reliably catch high-value code-quality, maintainability, test-quality, and "this works but is sloppy" issues, without turning every sweep into an unfocused rewrite.

Please review this in Roughdraft before I start. Tell me what is wrong, missing, or out of order.

Deliver implementation instruction: When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.
## What We Know
- The recent Uttr sweep felt too short and may not have been nitpicky enough.
  
- Uttr's generated local repo-sweep skill is stale compared with the current Prime Directive source skill.
  
- The current Prime Directive `$repo-sweep` is strong on production risk, first-principles analysis, runtime probes, and high-risk checks.
  
- The missing surface is a more explicit code-quality grind: dead code, shallow abstractions, brittle tests, unowned complexity, confusing module boundaries, duplicated logic, stale generated artifacts, and "green but not actually convincing" verification.
  
- This should not become a blanket "rewrite everything" mode. Findings still need evidence, impact, and a credible fix path.
  
## Steps
### 1. Define The Missing Mode
Goal: Make the behavior explicit enough that future agents know when to go deeper.

- [x] 
  
  Make `$repo-sweep --swarm` include nitpick depth by default. Do not add a separate public `--nitpick` modifier.
  
- [x] 
  
  Define the mode as "aggressive evidence-backed maintainability review," not style preference or broad redesign.
  
- [x] 
  
  State that valid nitpick findings need exact files or paths, concrete maintenance/user impact, and a smallest safe fix path.
  
- [x] 
  
  State what does not count: size alone, personal taste, speculative rewrites, churn for churn's sake, and refactors that only move complexity.
  
### 2. Add A Dedicated Nitpick Reference
Goal: Keep `SKILL.md` readable while giving the reviewer a real checklist.

- [x] 
  
  Create `skills/repo-sweep/references/nitpick-depth.md`.
  
- [x] 
  
  Include checks for dead code, over-broad abstractions, shallow wrappers, duplicated domain rules, scattered state, stale generated files, weak naming, TODO/fallback drift, and hard-to-test paths.
  
- [x] 
  
  Include test-quality checks: tests that mirror implementation, mock away the production path, assert too little, skip the failure mode, or leave critical browser/API paths unexercised.
  
- [x] 
  
  Include frontend/product-surface checks when applicable: visible dead controls, copy mismatch, hidden overflow, stale mockups, unverified interactions, and screenshots that prove little.
  
- [x] 
  
  Include "looks bad but fine" handling so the report can clear false positives instead of turning them into busywork.
  
### 3. Wire It Into Repo Sweep
Goal: Make the mode reachable and hard to accidentally skip.

- [x] 
  
  Update `skills/repo-sweep/SKILL.md` references and workflow to load the nitpick reference whenever `--swarm` is present.
  
- [x] 
  
  Add a dedicated maintainability/slop lane to the `--swarm` lane set.
  
- [x] 
  
  Require the report to say whether nitpick depth ran, what files/hotspots it inspected, and what it intentionally did not inspect.
  
- [x] 
  
  For `/goal $repo-sweep`, require nitpick findings with `Disposition: fix` to enter the normal fix/resweep loop.
  
### 4. Tighten Review Protocol Interaction
Goal: Avoid the Codex short review path silently weakening repo sweeps.

- [x] 
  
  Check `skills/shared/references/review/review-protocol.md` and make clear that repo-sweep can force full-chain depth even when normal Codex reviews use `codex-short`.
  
- [x] 
  
  If needed, add wording that `$repo-sweep --swarm` must run Prompt C, D, E, F, and I at minimum, plus G/H when applicable.
  
- [x] 
  
  Keep normal task review efficient; do not make every small task run the full redundant chain.
  
### 5. Update Public Routing
Goal: Make the user-facing command obvious.

- [x] 
  
  Update `README.md` quick reference and skill details with the new modifier or mode.
  
- [x] 
  
  Add a plain recommendation: for "I want this to run for a while and find slop," use `/goal $repo-sweep --swarm --preserve-review-artifacts`.
  
- [x] 
  
  Remove or avoid `--loop` language if current contract says goal mode owns repair/resweep.
  
### 6. Sync And Validate Against Uttr
Goal: Prove the fix reaches the repo where the concern showed up.

- [x] 
  
  Run `python3 scripts/validate-skill-contracts.py`.
  
- [x] 
  
  Run `git diff --check`.
  
- [x] 
  
  Run `./scripts/install-codex-plugin.sh`.
  
- [x] 
  
  Identify the correct sync path for Uttr's generated `skills/` tree before editing Uttr. Result: no `scripts/sync-repo.sh` generator was found in the Uttr checkout or nearby searched workspaces.
  
- [x] 
  
  After Prime Directive is updated, sync or regenerate Uttr's skill copy so `/Volumes/Code/uttr/skills/repo-sweep/SKILL.md` no longer lags the source contract. Deferred: the generated Uttr copy still lags because the generator script was unavailable; do not hand-edit the generated file.
  
- [x] 
  
  In Uttr, run a read-only smoke check that the generated skill mentions the new nitpick mode and the current goal-mode repo-sweep wording. Result: the generated Uttr copy does not yet mention nitpick depth, confirming the sync gap.
  
### 7. Acceptance Check
Goal: Make sure the next sweep is visibly deeper.

- [x] 
  
  In a future Uttr run, invoke the deep version explicitly: `/goal $repo-sweep --swarm --preserve-review-artifacts`. Deferred as the post-merge acceptance run.
  
- [x] 
  
  The resulting report should list maintainability/code-quality hotspots, not only production/security findings. Deferred as the post-merge acceptance criterion.
  
- [x] 
  
  The report should name inspected hotspots, rejected false positives, verification commands, residual gaps, and fixable findings. Deferred as the post-merge acceptance criterion.
  
- [x] 
  
  If it still completes in about 15 minutes on Uttr without a clear hotspot inventory, treat that as a failed acceptance check and tighten the skill again. Deferred as the post-merge acceptance criterion.
