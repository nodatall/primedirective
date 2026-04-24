# Deep Research Memo: Plan Refine Challenger Lane

web research status: complete

current_date: 2026-04-24
timezone: America/Los_Angeles

## Project Context Snapshot

Prime Directive is a documentation-first Codex plugin source repo. The planned change updates `$plan-refine`, a workflow skill that refines PRD/TDD/tasks-plan artifacts through fresh read-only reviewer subagents. The current stack is markdown skill contracts under `skills/`, shell installer scripts under `scripts/`, and a GitHub Actions validation workflow for Codex installer idempotence.

Highest-priority quality attributes: maintainability, workflow clarity, predictable stop conditions, token/runtime cost control, auditability, and avoiding extra user-question burden.

## Version-First Stack Discovery Notes

- `skills/plan-refine/SKILL.md` owns the primary plan-refine workflow.
- `skills/shared/references/execution/task-file-contract.md` mirrors refinement behavior for composition.
- `skills/plan-and-execute/SKILL.md` composes `$plan-refine` through `--refine-plan`.
- No `package.json`, `pyproject.toml`, or conventional test suite is present.
- `.github/workflows/validate.yml` validates `./scripts/install-codex-plugin.sh` idempotence on push/PR.
- README documents local installer checks.
- Exact Codex runtime version is not encoded in this repo; reasoning tiers are documented in `skills/shared/references/reasoning-budget.md`.

## External Query Privacy Notes

Searches used generic public terms about multi-agent orchestration, evaluation loops, reflection, debate patterns, prompt/output constraints, and AI risk management. No private repository content, unpublished business details, secrets, or user data were sent externally.

## Draft-Linked Research Agenda

| question_id | question | draft link | bucket | possible impact |
| --- | --- | --- | --- | --- |
| RQ-001 | Should the challenger be a separate specialist role or folded into the reviewer prompt? | TDD Architecture / `TDR-001` | core technical approach | Could change whether the workflow uses one or two subagents per refinement round. |
| RQ-002 | How should the workflow avoid agent theater, duplicate review, and unnecessary cost? | PRD Constraints / `FR-007`; TDD Failure Modes | limits, performance, cost | Could change cadence, stop rule, and whether challenger runs every round. |
| RQ-003 | What output contract makes challenger feedback auditable and actionable? | TDD Data Model / `TDR-003` | interfaces and schemas | Could change challenge brief fields and disposition logging. |
| RQ-004 | What safety/trust constraints matter when one agent critiques plans that may involve tools, private context, or user decisions? | TDD System Boundaries / Operational Readiness | security, privacy, operational readiness | Could change human-escalation rules and no-edit boundaries. |
| RQ-005 | What stopping condition should govern a challenger/reviewer loop? | PRD Success Criteria / `FR-006`; TDD Failure Modes | verification and failure handling | Could change whether challenger objections alone keep refinement alive. |

## Improvement Backlog

- Test whether the proposed challenger lane should be another reviewer or a distinct specialist.
- Validate the proposed default cadence: challenger in round 1, repeat only after blocker/material rounds.
- Strengthen the challenge brief schema so objections are concrete, not generic.
- Confirm the reviewer should be the severity gate.
- Ensure user questions stay limited to true unsafe/impossible-to-default blockers.

## Evidence Ledger

| source_id | source_type | source_family | url | publication_date | last_updated_date | accessed_date | version_or_scope | supported_claims | counts_toward_external_primary_minimum | current_enough_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | official docs | OpenAI | https://help.openai.com/en/articles/6654000-prompt-engineering-guide | unknown | 2026-04-23 inferred from "Updated: yesterday" on 2026-04-24 | 2026-04-24 | OpenAI prompt engineering guidance | Clear instructions and current-capability prompting matter; newest/capable models are easier to prompt. | yes | Official OpenAI help article updated immediately before this research date. |
| S2 | official docs | OpenAI Agents SDK | https://openai.github.io/openai-agents-js/guides/multi-agent/ | unknown | unknown | 2026-04-24 | OpenAI Agents SDK multi-agent orchestration | Specialist agents as tools keep a manager responsible for final synthesis; code orchestration supports chaining, critique, evaluator loops, and bounded subtasks. | yes | Official SDK documentation, current enough for architectural pattern guidance. |
| S3 | official docs | OpenAI API | https://developers.openai.com/api/docs/guides/evaluation-best-practices | unknown | unknown | 2026-04-24 | OpenAI evaluation best practices | Evaluation should use specific criteria, pass/fail thresholds, comparative judgment, and multiple reviewer signals where appropriate. | yes | Official OpenAI developer documentation for evaluation design. |
| S4 | engineering guidance | Anthropic | https://www.anthropic.com/engineering/building-effective-agents | 2024-12-19 | unknown | 2026-04-24 | Anthropic agent/workflow design guidance | Prefer simple composable patterns; add complexity only when it improves task performance; evaluator-optimizer fits clear criteria and measurable refinement value. | yes | Primary vendor engineering guidance and still directly relevant to agent workflow design. |
| S5 | official docs | Microsoft AutoGen | https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/reflection.html | unknown | unknown | 2026-04-24 | AutoGen stable reflection pattern | Reflection uses a generator plus reviewer loop with message protocols, approval/revision outputs, and stop conditions. | yes | Official Microsoft AutoGen stable documentation for multi-agent reflection. |
| S6 | official docs | Microsoft AutoGen | https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/multi-agent-debate.html | unknown | unknown | 2026-04-24 | AutoGen stable multi-agent debate pattern | Debate patterns need explicit roles, communication topology, finite rounds, and aggregator responsibility. | yes | Official Microsoft AutoGen stable documentation for debate orchestration. |
| S7 | government framework | NIST | https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook | 2022-07-08 | 2026-03-27 | 2026-04-24 | NIST AI RMF Playbook | Risk management should incorporate trustworthiness considerations into design, development, deployment, and use; guidance evolves with review. | yes | NIST page was updated less than one month before research. |
| S8 | security guidance | OWASP Gen AI Security Project | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | unknown | unknown | 2026-04-24 | OWASP LLM01:2025 Prompt Injection | Constrain model behavior, define and validate outputs, enforce least privilege, require human approval for high-risk actions, and conduct adversarial testing. | yes | OWASP Gen AI Security guidance is authoritative for LLM application risk controls. |

external_primary_sources_count: 8
source_family_count: 6

## Source Authority Notes

OpenAI and Anthropic sources are primary for agent-orchestration and prompt/workflow guidance from model providers. Microsoft AutoGen sources are primary for named multi-agent design patterns. NIST and OWASP are primary for risk management and LLM application safety guidance. Repo-local files remain authoritative for what Prime Directive currently does.

No source conflicts required reconciliation. The main tension is cost/complexity versus stronger review. Anthropic's simplicity guidance and OpenAI/Microsoft specialist-loop patterns reconcile cleanly as a bounded challenger lane, not an unbounded debate system.

## Findings By Bucket

### Core Technical Approach

Specialized roles are justified when the roles are meaningfully different. OpenAI Agents SDK guidance supports specialist agents used as tools while a manager keeps synthesis responsibility (S2). Anthropic's routing and evaluator-optimizer patterns support distinct prompts when different considerations need focused attention and clear feedback criteria exist (S4). AutoGen reflection supports a generator/reviewer loop with explicit message protocol and approval/revision state (S5).

Adopt now: keep the challenger as a distinct role, but do not let it become a second reviewer. The challenger produces adversarial objections; the reviewer classifies them.

### Interfaces, Schemas, And Output Contracts

OpenAI evaluation guidance emphasizes criteria and pass/fail thresholds instead of freeform vibes (S3). OWASP recommends defining and validating expected output formats for LLM systems (S8). AutoGen reflection shows the value of explicit message structures for review tasks, including result fields and approval state (S5).

Adopt now: require a compact challenge brief schema and reviewer disposition fields in the refinement log.

### Limits, Performance, And Cost

Anthropic warns that agentic systems trade latency and cost for performance and should remain simple unless complexity is warranted (S4). OpenAI notes manager-style orchestration can combine specialist outputs while enforcing shared guardrails (S2).

Adopt now: challenger runs in round 1 and repeats only when the previous reviewer round found blocker/material issues. Do not run challenger-only loops.

### Security, Privacy, And Operational Readiness

OWASP recommends constrained behavior, least privilege, human approval for high-risk actions, segregating untrusted content, and adversarial testing (S8). NIST frames AI risk management as design/development/deployment/use concerns, not a final-only check (S7).

Adopt now: keep challenger/reviewer read-only, main agent as sole artifact editor, and user escalation limited to unsafe/impossible-to-default blockers.

### Verification And Failure Handling

OpenAI evaluation guidance supports explicit scorecards and thresholds (S3). AutoGen reflection and debate docs show loops require stop conditions and aggregator responsibility (S5, S6). Anthropic notes agents should use stopping conditions such as max iterations to maintain control (S4).

Adopt now: preserve the existing reviewer-owned stop rule. Challenger objections do not keep refinement alive unless the reviewer promotes them to blocker/material.

## Adopt-Now, Watchlist, Avoid

Adopt now:

- Role-separated challenger then reviewer flow.
- Challenger brief with required fields and no approval-only output.
- Reviewer-owned severity classification and stop rule.
- Main-agent-only edits and disposition logging.
- Bounded cadence to control cost and noise.

Watchlist:

- A future machine-readable challenge schema if Prime Directive later adds executable validation for skill contracts.
- Parallel challenger/reviewer execution only if later evidence shows the reviewer can reliably classify challenge briefs after independent review without losing context.

Avoid:

- A public `$grill-me` skill for this change.
- Multi-agent debate rounds without a concrete artifact-change/disposition contract.
- Challenger objections that automatically become edits without reviewer filtering.
- Challenger loops that continue after clean reviewer rounds.

## Finding-to-Artifact Delta

| finding_id | research_question_id | bucket | disposition | recommendation | recommendation_level | support_type | source_ids | prd_tdd_sections_changed | task_plan_inputs_created | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | RQ-001 | core technical approach | adopted | Add a separate challenger lane before reviewer classification. | adopt now | synthesis across official/vendor docs | S2, S4, S5 | TDD Architecture / Approach, `TDR-001` | Update `skills/plan-refine/SKILL.md` role/cadence docs. | Specialized roles are useful when prompts have distinct jobs. |
| F-002 | RQ-002 | limits, performance, cost | adopted | Bound cadence to round 1 plus later blocker/material rounds. | adopt now | synthesis | S2, S4 | PRD Constraints, TDD Failure Modes | Add explicit cadence and no challenger-only loop rules. | Controls cost and avoids duplicate review. |
| F-003 | RQ-003 | interfaces and schemas | adopted | Define challenge brief and reviewer disposition fields. | adopt now | directly supported | S3, S5, S8 | TDD Data Model, `TDR-003` | Update refinement log contract in `plan-refine` and `task-file-contract`. | Explicit criteria/fields make feedback auditable. |
| F-004 | RQ-004 | security and operational readiness | adopted | Preserve read-only subagents, main-agent-only edits, and rare user escalation for unsafe blockers. | adopt now | synthesis | S7, S8 | TDD System Boundaries, Operational Readiness | Add trust-boundary language to challenger workflow. | Prevents critiques from becoming uncontrolled actions. |
| F-005 | RQ-005 | verification and failure handling | adopted | Keep reviewer-owned stop rule; challenger objections need reviewer promotion to continue. | adopt now | synthesis | S3, S4, S5, S6 | PRD Success Criteria, TDD Failure Modes | Add stop-rule clarification to `plan-refine` and task contract. | Stop conditions prevent debate loops. |

## Research Output Summary

The research supports the user's intuition that a challenger role can surface different issues only if it is explicitly specialized. The best design is not open-ended debate. It is a bounded challenger brief feeding the existing reviewer severity gate, with the main agent retaining synthesis and artifact-editing control.

## Plan-Specific Implementation Checklist

- Define challenger as fresh, read-only, and adversarial.
- Prohibit `looks good` / approval-only challenger output.
- Require a compact challenge brief with actionable objections and counter-plan pressure.
- Pass the challenge brief to the normal reviewer.
- Keep the reviewer as the severity and stop-rule owner.
- Record accepted/rejected/deferred/superseded challenge dispositions in the refinement log.
- Mirror composition-relevant behavior in `task-file-contract.md`.
- Keep `$plan-and-execute` wording thin.

## Risks Or Unknowns That Remain

- There is no executable test harness for skill semantics, so verification is by text review, installer idempotence, and final review.
- Actual usefulness of the challenger lane should be measured on future `$plan-refine` examples; one clean implementation does not prove permanent value.

## Deep Research Completion Stamp

- external_primary_sources_count: 8
- source_family_count: 6
- research_questions_answered: 5
- buckets_reviewed: 5
- follow_up_passes_completed: 2
- adopted_findings_count: 5
- rejected_or_deferred_findings_count: 0
- prd_tdd_sections_changed: PRD Constraints and Success Criteria; TDD Architecture / Approach, Data Model, Technical Requirements, Failure Modes, Operational Readiness
- task_plan_inputs_created: challenger role/cadence update, challenge brief schema, reviewer handoff/disposition update, task-file contract mirror, plan-and-execute thin wording review, validation checks
- evidence_bar_met: yes
