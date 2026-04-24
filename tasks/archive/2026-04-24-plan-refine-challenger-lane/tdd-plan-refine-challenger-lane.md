# Plan Refine Challenger Lane TDD

## Plain-Language Summary

`$plan-refine` already asks a fresh reviewer to check whether a PRD, TDD, and task plan are ready to execute. This change adds a different internal role: a challenger that tries to break the plan before the reviewer judges it.

The challenger should not ask the user more questions by default. It should inspect the artifacts, name hidden assumptions and likely failure points, then let the normal reviewer decide which objections are real blocker or material issues.

The final result should make plans harder to fool without adding a new public command or noisy debate theater. The workflow should stay simple for the user while giving the refinement loop a sharper adversarial pass.

## Technical Summary

Update Prime Directive skill documentation so `$plan-refine` runs an internal adversarial challenge lane before the existing reviewer lane. The challenger produces a compact challenge brief; the reviewer receives that brief and converts only valid issues into the existing structured findings format. The main agent applies accepted blocker/material fixes and records challenge dispositions in the refinement log.

## Scope Alignment to PRD

This design covers `FR-001` through `FR-013` by updating the documented `$plan-refine` workflow, shared task-file contract, and thin `$plan-and-execute` composition notes where needed. It does not change `$plan-work --grill` behavior and does not add a new public skill invocation.

## Current Technical Diagnosis

Current `$plan-refine` behavior is defined primarily in `skills/plan-refine/SKILL.md`. Shared workflow semantics for plan refinement are also duplicated in `skills/shared/references/execution/task-file-contract.md`, and `$plan-and-execute` references `$plan-refine` from `skills/plan-and-execute/SKILL.md`.

The repository is documentation-first. There is no package manifest or conventional test suite. Existing validation consists of the GitHub Actions installer idempotence workflow in `.github/workflows/validate.yml`, local installer smoke checks from `README.md`, and standard text checks such as `git diff --check`.

## Architecture / Approach

Use a role-separated two-lane refinement round:

1. Challenger lane: one fresh read-only challenger subagent runs before reviewer judgment for applicable rounds and returns a compact challenge brief.
2. Reviewer lane: one fresh read-only reviewer subagent runs the normal `$plan-refine` first-principles/audit review first, then adjudicates the challenge brief and produces the existing structured findings plus challenge dispositions.
3. Main-agent synthesis: the main agent applies accepted blocker/material fixes, records dispositions, and keeps the existing stop rule.

The challenger is deliberately adversarial and not balanced. The reviewer remains balanced and owns severity classification.

Research-backed rationale: OpenAI's agent orchestration guidance supports specialized agents as bounded helpers while a manager owns final synthesis (`S2` in `tasks/tmp/research-plan-plan-refine-challenger-lane.md`). Anthropic's agent guidance favors simple composable workflows and separate focused calls when distinct considerations improve quality (`S4`). AutoGen's reflection pattern supports explicit reviewer feedback loops with stop conditions (`S5`). For this repo, that means challenger and reviewer should be separate prompts with separate outputs, but the main agent remains the orchestrator.

## System Boundaries / Source of Truth

`skills/plan-refine/SKILL.md` is the source of truth for the plan-refine workflow. `skills/shared/references/execution/task-file-contract.md` must mirror the workflow contract where other skills need to compose or infer plan-refine behavior. `skills/plan-and-execute/SKILL.md` should remain a thin orchestrator and should not duplicate challenger mechanics beyond noting that `$plan-refine` owns them.

## Dependencies

- Subagent availability remains required for `$plan-refine`.
- No new external runtime dependency is introduced.
- The existing reasoning-budget reference controls challenger and reviewer reasoning tiers.
- Deep research and Pro synthesis memos must remain available through refinement when those modifiers are used.

## Route / API / Public Interface Changes

No public command syntax changes.

`$plan-refine`, `plan-key=<plan-key>`, `--max-rounds=<n>`, and `--preserve-refine-artifacts` remain unchanged. `$plan-and-execute --refine-plan` remains unchanged.

## Data Model / Schema / Storage Changes

The refinement log contract gains a challenger section for each applicable round:

- `challenge_brief`
- `challenger_objections`, keyed by `challenge_id`
- `reviewer_dispositions`, keyed by `challenge_id`
- `artifact_changes_from_challenges`
- `rejected_or_deferred_challenges`

This is a markdown log structure, not a machine-readable schema.

Challenger brief fields:

- `challenge_id`
- `pressure_type`
- `artifact_refs`
- `hidden_assumption_or_failure_mode`
- `how_it_could_break_execution`
- `evidence_or_gap`
- `counter_plan_pressure`
- `suggested_reviewer_test`
- `requires_user_decision_candidate`: `yes` or `no`

Do not include challenger severity. The reviewer owns severity. A valid empty brief is allowed only as `no_material_challenges_found: yes` with a one-sentence rationale; the challenger may not invent objections to satisfy the role.

Allowed reviewer dispositions for challenge IDs:

- `promoted_to_finding`
- `already_covered`
- `non_material`
- `rejected`
- `superseded`
- `deferred_with_owner`

`deferred_with_owner` must name where the issue is carried: TDD obligation, task-plan step, explicit non-goal, or accepted residual risk. Blocker-grade issues may not be deferred instead of fixed or escalated.

Research-backed rationale: OpenAI's evaluation guidance emphasizes specific criteria and thresholds (`S3`), OWASP recommends defined/validated output formats for LLM systems (`S8`), and AutoGen's reflection docs use explicit review result fields (`S5`). The markdown log does not need a strict JSON schema, but it does need stable headings and required fields so later agents can audit whether challenger objections were acted on or intentionally rejected.

## Technical Requirements (`TDR-*`)

- `TDR-001`: `skills/plan-refine/SKILL.md` must define challenger role, cadence, no-edit rule, output schema, and reviewer handoff.
- `TDR-002`: The challenger lane must use a fresh read-only subagent and strongest appropriate reasoning tier, matching plan-refine's reviewer isolation standard.
- `TDR-003`: The reviewer lane must receive the challenge brief and classify objections through the existing `blocker` / `material` / `minor` finding model, plus explicit rejection/defer/supersede dispositions where needed.
- `TDR-004`: The main agent must update only PRD, TDD, tasks-plan, and the refinement log during plan refinement.
- `TDR-005`: The fixed stop rule must remain unchanged and reviewer-owned.
- `TDR-006`: `skills/shared/references/execution/task-file-contract.md` must mirror any composition-relevant challenger behavior so `$plan-and-execute --refine-plan` and future workflow readers do not miss it.
- `TDR-007`: `skills/plan-and-execute/SKILL.md` must stay thin and only reference the improved `$plan-refine` behavior if needed for clarity.
- `TDR-008`: Validation must include `git diff --check`, installer idempotence smoke checks, and a final review of skill invocation surfaces.
- `TDR-009`: `$plan-and-execute` must hard-stop when `$plan-refine` fails due to missing artifacts, failed evidence or Pro gates, unavailable challenger/reviewer subagents, incomplete challenge dispositions, or unsafe/impossible-to-default blockers.
- `TDR-010`: `$plan-and-execute` may continue through recoverable churn only when no reviewer blocker/material findings remain and the safest artifact fix or accepted residual risk is recorded. Max-round stops with unresolved reviewer blocker/material findings are hard stops.
- `TDR-011`: When `$plan-refine` runs under `$plan-and-execute`, keep `tasks/tmp/plan-refine-<plan-key>.md` available through final full-branch review and finalization; then clean it unless preservation is active.
- `TDR-012`: Every `challenge_id` must receive a reviewer disposition before edits, stop decisions, or clean completion.
- `TDR-013`: Refinement outcome taxonomy must be explicit: clean success can continue; recoverable churn can continue only with no unresolved reviewer blocker/material findings and a recorded safe residual assumption; max-round stops with unresolved blocker/material findings are hard stops.

## Ingestion / Backfill / Migration / Rollout Plan

This is a docs/skill contract change. Rollout means installing the updated Prime Directive plugin locally with `./scripts/install-codex-plugin.sh` after changes land. Existing planning artifacts do not require migration.

## Failure Modes / Recovery / Rollback

- If the challenger is underspecified, future agents may treat it as another generic reviewer. Mitigation: make the challenger prompt prohibit approval-only output and require strongest objections/counter-plan pressure.
- If the challenger is over-specified, it may create noisy debates and token cost without artifact improvement. Mitigation: require reviewer filtering and artifact-change or disposition logging.
- If the reviewer only adjudicates challenger claims, the normal `$plan-refine` audit weakens. Mitigation: require reviewer normal audit first, then challenge adjudication.
- If a challenger objection lacks disposition, the refinement log becomes non-auditable. Mitigation: require a corrected reviewer response for the same round before proceeding.
- If `$plan-and-execute` treats all refinement failures as recoverable, execution may start after a failed required lane. Mitigation: split hard-stop and recoverable outcomes.
- If max-round behavior is described as recoverable without excluding unresolved blocker/material findings, `$plan-and-execute` can contradict standalone `$plan-refine`. Mitigation: define max-round with unresolved blocker/material findings as a hard stop.
- If shared contract docs are not updated, `$plan-and-execute --refine-plan` consumers may miss the behavior. Mitigation: update `task-file-contract.md` and keep `$plan-and-execute` thin.
- Rollback is reverting the documentation changes to `skills/plan-refine/SKILL.md`, `task-file-contract.md`, and any thin orchestrator wording.

Research-backed rationale: Anthropic's guidance warns to keep agent workflows simple and composable unless added complexity improves outcomes (`S4`). AutoGen debate/reflection patterns rely on explicit topology and stopping conditions (`S5`, `S6`). The challenger cadence is a repo-specific design judgment informed by those cost/control principles, not a directly source-proven best practice. The challenger must therefore be bounded by cadence and reviewer-owned stop rules rather than creating a second open-ended loop.

## Operational Readiness

No production deployment or runtime service is affected. The operational concern is skill distribution: rerun `./scripts/install-codex-plugin.sh` and, if needed, verify skill visibility in a fresh Codex thread.

Research-backed rationale: NIST's AI RMF Playbook frames trustworthy AI behavior as a design and development concern, not only a final deployment concern (`S7`). OWASP LLM guidance recommends constrained behavior, validated outputs, least privilege, human approval for high-risk actions, and adversarial testing (`S8`). For this repo, the direct application is read-only challenger/reviewer agents, main-agent-only edits, and rare user escalation only for unsafe blockers.

## Verification and Test Strategy

Validation commands and checks:

- `git diff --check`
- `HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh`
- `HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh` twice against the same temp home to verify idempotence
- `./scripts/install-codex-plugin.sh`
- Manual documentation review of `README.md`, `skills/plan-refine/SKILL.md`, `skills/shared/references/execution/task-file-contract.md`, and `skills/plan-and-execute/SKILL.md`

Failing-test-first is not practical for this documentation-only skill contract change because there is no executable parser or test harness for skill semantics. The closest red/green proxy is to inspect the pre-change docs and verify that no challenger lane exists before editing, then run text/installer validation after editing.
