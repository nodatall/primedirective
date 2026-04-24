# Plan Refine Challenger Lane PRD

## Plain-Language Summary

`$plan-refine` already asks a fresh reviewer to check whether a PRD, TDD, and task plan are ready to execute. This change adds a different internal role: a challenger that tries to break the plan before the reviewer judges it.

The challenger should not ask the user more questions by default. It should inspect the artifacts, name hidden assumptions and likely failure points, then let the normal reviewer decide which objections are real blocker or material issues.

The final result should make plans harder to fool without adding a new public command or noisy debate theater. The workflow should stay simple for the user while giving the refinement loop a sharper adversarial pass.

## Target User / Audience

Prime Directive users who rely on `$plan-refine` or `$plan-and-execute --refine-plan` to improve planning artifacts before implementation.

## Problem Statement

The current `$plan-refine` reviewer is strong at checking whether artifacts are executable, complete, and internally aligned. It can still miss a different class of problem: a plan that looks coherent but rests on false settled decisions, hidden defaults, implementation drift traps, or an unnecessarily broad solution shape.

## Current-State / Product Diagnosis

`$plan-refine` currently spawns one fresh read-only reviewer subagent per round. That reviewer produces structured blocker/material/minor findings, and the main agent applies blocker/material fixes until a fresh reviewer round finds no blocker or material issues.

This is useful, but the reviewer role is intentionally balanced. The proposed challenger role is intentionally adversarial. It should look for what the plan is pretending is settled, what would break, what an implementation agent would misread, and what another reviewer might miss.

## Product Goal

Add a default internal adversarial challenger lane to `$plan-refine` so refinement surfaces hidden assumptions and counter-plan pressure before the normal reviewer produces structured findings.

## Success Criteria

- `$plan-refine` remains the public workflow; no new required flag is introduced.
- `$plan-and-execute --refine-plan` automatically benefits because it composes `$plan-refine`.
- The challenger role is clearly different from the reviewer role.
- The challenger produces actionable objections, not generic approval or duplicate review prose.
- The reviewer receives the challenge brief and filters it into the existing blocker/material/minor finding structure.
- The stop rule remains based on the reviewer finding no blocker or material issues.
- Every challenger objection is dispositioned before a clean stop.
- User questions remain rare and limited to unsafe or impossible-to-default blockers.

## Explicit Non-Goals

- Do not create a standalone `$grill-me` or `$challenge-plan` skill.
- Do not change `$plan-work --grill` user-questioning behavior.
- Do not add public stop-threshold knobs or new required modifiers.
- Do not make two agents produce competing edit lists.
- Do not require a challenger on every clean later round when the previous round found no blocker or material issues.
- Do not add runtime code, UI, or external service dependencies.

## User Stories or Primary User Outcomes

- As a user, I can keep invoking `$plan-refine` the same way and get stronger plan pressure-testing.
- As a user, I can invoke `$plan-and-execute --refine-plan` and know the plan was challenged before execution.
- As an implementation agent, I receive artifacts that have already been tested for false assumptions, drift traps, and overbuilt scope.
- As a reviewer, I can see whether adversarial objections were accepted, rejected, deferred, or superseded.

## Functional Requirements (`FR-*`)

- `FR-001`: `$plan-refine` must include an internal adversarial challenger lane that runs before normal reviewer judgment in applicable rounds.
- `FR-002`: The challenger lane must produce a compact challenge brief focused on hidden assumptions, false settled decisions, implementation drift traps, failure paths, overengineering, under-specification, and counter-plan pressure.
- `FR-003`: The challenger must not edit artifacts, rewrite plans, or continue into another round.
- `FR-004`: The reviewer must receive the challenge brief and decide which challenger objections become blocker, material, minor, rejected, deferred, superseded, or non-material findings.
- `FR-005`: The main agent must record challenger dispositions in the refinement log when they lead to changes or are materially rejected/deferred.
- `FR-006`: The fixed stop rule must remain reviewer-owned: stop when a fresh reviewer round finds no blocker or material issues.
- `FR-007`: The workflow must preserve the current simple public interface and existing round cap behavior.
- `FR-008`: User-facing questions must not increase except for true blockers that are unsafe, contradictory, or impossible to default.
- `FR-009`: The reviewer must run the normal `$plan-refine` audit before adjudicating the challenge brief so challenger claims do not replace or anchor the full review.
- `FR-010`: Challenge dispositions must be constrained so a blocker-grade issue cannot disappear behind vague deferral.
- `FR-011`: `$plan-and-execute --refine-plan` must distinguish recoverable refinement residual-risk outcomes from hard-stop failures before execution continues.
- `FR-012`: When `$plan-refine` runs inside `$plan-and-execute`, the refinement log must remain available through final full-branch review and finalization unless a blocker prevents completion.
- `FR-013`: `$plan-and-execute` may continue after refinement only when the refinement outcome is clean success or recoverable churn with no unresolved reviewer blocker/material findings.

## Acceptance Criteria

- For `FR-001` through `FR-004`, `skills/plan-refine/SKILL.md` defines the challenger role, run cadence, challenge brief schema, reviewer handoff, and no-edit constraints.
- For `FR-005`, `skills/plan-refine/SKILL.md` and any relevant shared task-file contract language require challenge dispositions in `tasks/tmp/plan-refine-<plan-key>.md`.
- For `FR-006`, the existing stop rule remains unchanged and explicitly states that challenger objections do not keep the loop alive unless the reviewer promotes them to blocker/material.
- For `FR-007`, README invocation syntax and supported modifiers remain stable.
- For `FR-008`, user-question language remains constrained to unsafe or impossible-to-default blockers.
- For `FR-009`, reviewer instructions explicitly require normal audit findings before challenge adjudication.
- For `FR-010`, allowed dispositions include concrete carry-forward ownership and prohibit blocker-grade deferral.
- For `FR-011`, `$plan-and-execute` and `task-file-contract.md` define which refinement failures hard-stop execution.
- For `FR-012`, the refinement log cleanup timing is documented for both standalone `$plan-refine` and `$plan-and-execute`.
- For `FR-013`, max-round stops with unresolved blocker/material findings remain hard stops; recoverable churn is limited to cases with recorded safe residual assumptions and no unresolved blocker/material findings.
- Repository verification passes with `git diff --check` and installer idempotence checks.

## Product Rules / UX Rules / Content Rules

- Describe the new role as an adversarial challenger or challenger lane, not as a user-facing grill mode.
- Keep documentation concise and operational; avoid debate-for-debate's-sake language.
- Use concrete artifact terms: PRD, TDD, tasks-plan, challenge brief, reviewer findings, refinement log.
- Keep the public skill surface simple.

## Constraints and Defaults

- Default behavior: run the challenger in round 1.
- Later-round behavior: run the challenger when `round == 1 OR previous_reviewer_round_had_blocker_or_material`; do not continue challenger-only loops after a clean reviewer round.
- The reviewer remains the severity gate.
- The main agent remains the only actor that edits artifacts.
- The main agent may apply challenger-derived changes only after reviewer promotion to blocker/material, except for minor coherence edits needed after an accepted blocker/material fix.
- Refinement outcome taxonomy: clean success may continue; recoverable churn may continue only with no unresolved reviewer blocker/material findings and a recorded safe residual assumption; missing artifacts, failed research/Pro gates, unavailable challenger/reviewer subagents, incomplete challenge dispositions, unsafe blockers, and unresolved blocker/material findings at max rounds are hard stops.
- The work is documentation/skill-contract only unless research or Pro analysis identifies a necessary adjacent contract update.
- The challenger lane must stay bounded and composable: it is added only where it improves artifact quality, and it must not become a general-purpose debate loop.

## Success Metrics / Guardrails

- The final workflow text makes it hard for agents to collapse the challenger into a duplicate reviewer.
- The final workflow text makes it hard for agents to treat challenger objections as automatic changes without reviewer filtering.
- The refinement log has enough structure to audit accepted and rejected challenges.
- The final `$plan-refine` summary surfaces challenger-sourced material fixes or residual accepted challenge risks when any exist.
- No existing activation names or public modifiers are broken.
