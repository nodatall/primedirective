# Reduce Skill Context And Repeated Approval

Goal: Make Prime Directive skills easier to discover and cheaper to load, and carry explicit implementation authorization through completed analysis and review stages.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## Context

- This plan covers the four recommendations from the skill audit: duplicate discovery, description routing, selective reference loading, and repeated approval.
- The current Codex session exposes all 19 Prime Directive skills through both the plugin and direct links. The installer creates both, and generated team setup guidance checks the direct Deliver link.
- `review-plan` currently loads complete Deliver, Plan-refine, and First-principles entry points. Its entry point and directly required references total about 12,000 words before the target plan is read.
- Implementation uses a separate feature worktree based on `ab611781a1c480e8a2dc8c73f0378f42dde013c2`. Preserve the existing Deliver rewrite's frozen evaluation, other execution plans, and unrelated working-tree files. Recheck the source state before creating that worktree; do not absorb later changes automatically.
- Keep current testing standards, review rounds, completion gates, public commands, and Claude installation behavior. The authorization handoff in step 5 is the only intended workflow behavior change.

## Steps

### 1. Preserve the comparison baseline

- [ ] Prepare the isolated implementation worktree and capture its own finalization baseline before copying this execution plan into it. Record required runtime and environment availability; prepare any required ignored configuration explicitly.
- [ ] Preserve the baseline skill packages and freeze a small set of realistic routing, reference-loading, and authorization scenarios before changing the candidate. Include positive cases and neighboring requests that must not activate the changed behavior. Record discovery counts, description lengths, and the full required-reference footprint for the selected workflows.

### 2. Install each Codex skill once

- [ ] Make the plugin the canonical Codex discovery surface. Stop creating direct skill links and remove only links proven to belong to this install after the plugin refresh and skill availability checks succeed. Preserve user directories, foreign links, and unrelated plugin configuration; retain the existing links when refresh or verification fails.
- [ ] Update setup output, README installation guidance, and generated team-install checks to recognize the working plugin installation. Keep Claude checks host-specific and ensure a stale cache directory alone cannot count as an enabled Codex installation.
- [ ] Verify fresh installation, migration, repeated installation, plugin failure, and preservation of user-owned paths with isolated fixtures. Verify all 19 skills and their required references are discoverable through the real Codex plugin before retiring the local compatibility links. Check generated team guidance against that plugin-only installation.

### 3. Make descriptions select the right workflow

- [ ] Shorten the public skill descriptions where needed so each starts with its distinctive task and selection boundary. Put Plan-to-goal's adaptive-loop condition first and identify Plan-refine as legacy-artifact-only. Keep modifiers and detailed output formats in the skill body without losing supported invocation paths.
- [ ] Align affected README and validator metadata with the descriptions. Run the frozen routing cases against baseline and candidate, including active Deliver plans versus legacy plans, adaptive goals versus fixed checklists, and ordinary requests that should not trigger a heavyweight workflow.

### 4. Load only the contracts a stage needs

- [ ] Move the large artifact templates, reviewer schemas, and completion-stamp detail from `plan-to-goal`, `plan-refine`, and `review-plan` into their owned references. Keep activation, routing, workflow order, and stop gates visible in each entry point.
- [ ] Replace Review-plan's complete parent-workflow imports with direct references to the plan format, bounded refinement rules, and council rules it actually consumes. Reuse existing owners where possible; extract shared detail once when needed, and update every affected consumer and ownership check.
- [ ] Verify all reference paths in both source and installed packages. Compare the complete instructions required by the frozen scenarios, including nested references: reduce irrelevant required reading while retaining every applicable rule, template field, and machine-facing token.

### 5. Continue when implementation is already authorized

- [ ] Update First-principles-mode, Review-plan, their affected owner references, and Deliver's handoff wording so an explicit request to analyze or review and then implement can continue through the authorized implementation workflow after the stage succeeds. Prior authorization must still apply to the current scope; material scope changes or unresolved implementation decisions require a new decision.
- [ ] Keep the analysis stage read-only and Review-plan limited to its permitted plan and review-log edits. Complete the stage and its existing completion record before handing control back to implementation. Preserve analysis-only requests, review-only requests, explicit approval gates, and bare Deliver's normal initial plan-review pause; a plan-fix approval alone does not authorize implementation.
- [ ] Verify same-request and prior-authorization continuation, cancellation or superseding restrictions, unapproved proposed fixes, newly material decisions, and missing verification. Preserve the review-stage meaning of `implementation_started: no`; subsequent execution belongs to the resumed implementation workflow.

### 6. Validate and finish

- [ ] Use the existing Skill Review workflow for fresh baseline/candidate runs and an independent judgment on the changed behavior. Require correct routing, preserved stage boundaries and completion rules, less irrelevant required context, and continuation only in explicitly authorized cases. Record inconclusive evidence as incomplete; do not treat shorter files or lower word counts alone as proof of improvement.
- [ ] Run focused installer and generated-guidance checks, affected skill checks, `python3 scripts/validate-skill-contracts.py`, and `git diff --check`. Install the verified candidate with `./scripts/install-codex-plugin.sh` and inspect the actual Codex skill catalog. Report any discovery behavior that cannot be verified in the live app.
- [ ] Complete a fresh final review, repair verified in-scope findings, and rerun affected checks. Archive this plan, commit only this work, and complete Deliver finalization in the implementation worktree. Preserve the source checkout and the separate Deliver evaluation.
