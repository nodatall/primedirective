# Rule: Deep Research for Planning

## Goal

Run a focused draft-improvement research pass when the planning trigger includes `--deep-research`.

This pass exists to strengthen drafted PRD and TDD before tasks-plan is generated. It should reduce avoidable implementation mistakes, missing rollout work, and weak verification strategy.

This mode is not satisfied by a token burst of a few searches. Treat `--deep-research` as a substantial, web-backed research pass with a real evidence bar before tasks-plan may be drafted and before PRD/TDD may be treated as final.

Treat this as a current-state research task, not a timeless brainstorming task. The prompt and memo must stay anchored to the actual run date and the project's concrete stack, constraints, and risk areas.

## Accepted activation suffixes

- `--deep-research`
- `--preserve-planning-artifacts`

Planning activation form:

- `$plan-work [--deep-research] [--preserve-planning-artifacts]` with the source plan in the same request
- `$plan-and-execute [--deep-research] [--preserve-artifacts]` with the source plan already present in the current thread; this composes `$plan-work --from-thread --direct --deep-research` and then continues into execution without a revised-summary checkpoint

## When to run

Run this only after Socratic refinement has locked:

- `Goal`
- `Context`
- `Constraints`
- `Done when`
- the standalone summary checkpoint, unless `--direct` is active

Run it after generating initial drafts of:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`

Run it before generating:

- `tasks/tasks-plan-<plan-key>.md`

Before the first external search, capture the exact current date in the working materials and use it in the research framing.

## Default research scope

Deep research defaults to `Tech + Delivery`, not broad product discovery.

Cover these areas when relevant:

- technical design and architecture patterns
- route, API, interface, schema, and storage best practices
- migration, backfill, rollout, rollback, and recovery concerns
- security, operational readiness, and dependency concerns
- verification strategy, edge cases, and regression protection

Do not expand into broad market research or product discovery unless the source plan clearly depends on it.

## Research framing requirements

Before starting web research, explicitly frame the pass with:

- today's exact date
- the project timezone when known
- the product or workflow being changed
- the concrete frontend/backend/platform stack involved
- the highest-priority quality attributes for this plan, such as performance, accessibility, maintainability, security, operability, or migration safety
- the constraints that narrow the research, such as browser support, hosting model, framework version, legacy boundaries, compliance needs, or team conventions

Do not send a generic "latest best practices" prompt. Research must be scoped to the actual plan, current drafts, and technical environment.

## Version-first and privacy rules

Before the first external search:

- inspect repo manifests, lockfiles, configs, package files, deployment files, and existing docs enough to identify the relevant framework, SDK, database, provider, runtime, hosting, and validation versions
- record unknown versions explicitly instead of assuming the latest version
- include known versions or provider constraints in external queries when they materially affect the answer
- do not send secrets, private customer data, unpublished business details, proprietary identifiers, or large private snippets into web searches or external research prompts
- redact private project details before external searches; prefer stack-, provider-, version-, and behavior-specific queries

## Research process

1. Start from the locked planning decisions plus the current PRD/TDD drafts, not from a blank prompt.
2. Review the source plan and current PRD/TDD drafts to identify the highest-risk technical and delivery questions that could change implementation quality or sequencing.
3. Write a Draft-Linked Research Agenda first:
   - the main technical questions to answer
   - the highest-risk unknowns
   - which research buckets apply to this plan
   - the exact current date being used for freshness-sensitive questions
   - the stack-, provider-, or framework-specific areas that need current verification
   - the draft assumption, PRD section, TDD section, `FR-*`, or `TDR-*` each question could change
4. Create a temporary working memo at `tasks/tmp/research-plan-<plan-key>.md` while the research pass is in progress.
5. Seed the working memo with an improvement backlog:
   - draft weaknesses or assumptions to test
   - candidate improvements or alternatives to validate
   - the expected impact of each candidate on PRD, TDD, or task sequencing
6. Research in multiple passes, not one search burst:
   - first pass: official docs and primary references for the core stack or provider
   - second pass: operational constraints, failure modes, limits, rollout, and verification guidance
   - third pass: any plan-specific edge areas uncovered by the first two passes
7. For major recommendations, compare at least 2 independent relevant sources when possible.
8. Record source freshness for every substantive external source:
   - publication date when available
   - last-updated date when available
   - why the source is current enough for the claim being supported
9. Separate findings into:
   - widely accepted standards or official requirements
   - current best practices suitable to adopt now
   - emerging trends worth watching but not defaulting to
   - outdated or weak advice to avoid
10. Prefer primary sources for technical claims:
   - official documentation
   - vendor documentation
   - standards or specifications
   - primary technical references
11. Use live web research. It is required for every `--deep-research` run.
12. Start with external primary sources in the first pass. Repo-local sources are supplemental context, not a substitute for the external evidence bar.
13. If tooling and time allow, use at least 2 independent research passes or viewpoints for non-trivial design decisions, then reconcile conflicts in the working memo.
14. Explicitly mark which conclusions are:
   - directly supported by cited sources
   - synthesis across multiple sources
   - inference or judgment calls made for this specific plan
15. If live web research is unavailable at runtime, stop immediately and tell the user that `--deep-research` cannot proceed without web access.
16. Do not create a local-only exception for narrowly scoped or repo-heavy tasks. If the user wants a faster repo-only pass, they should use planning without `--deep-research`.
17. Budget a real deep pass, typically around 20-30 minutes for non-trivial plans, and do not treat the pass as complete until the completion checks below are met.
18. End the research pass by triaging the working memo:
   - choose the highest-value findings to adopt
   - note meaningful ideas rejected or deferred and why
   - update PRD/TDD before tasks-plan generation
   - distill the plan-specific checklist items and decisions worth carrying into this plan's execution
19. If research would materially change product behavior, external scope, or business intent, stop and ask one targeted follow-up question before finalizing artifacts.
20. If research materially changes the previously approved plain-language summary, present one revised standalone summary checkpoint before `tasks-plan` generation, except when the caller is `$plan-and-execute --deep-research`; in that direct orchestration flow, adopt the findings into the artifacts and continue unless the change is a true blocker that is unsafe, contradictory, or impossible to default.

## Minimum evidence bar

Before deep research may be considered complete, gather and record:

- at least 5 substantive external primary web source reviews
- repo-local source reviews as needed for implementation grounding, but never as a substitute for the external minimum
- at least 3 distinct research questions answered for this plan
- each research question linked to a draft assumption, PRD section, TDD section, `FR-*`, or `TDR-*` it could change
- at least 4 applicable buckets reviewed from the default scope, unless the plan is genuinely too narrow for that many
- at least 2 rounds of follow-up research after the initial source pass
- explicit notes on at least 3 design-impacting findings, not just links
- source-date metadata for every substantive external source
- at least 1 section that distinguishes adopt-now guidance from watchlist or avoid guidance
- at least 1 plan-specific checklist or implementation guidance section derived from the findings

Do not waive these minimums for narrow or local-only tasks when `--deep-research` is present.

## Source count and authority rules

An external primary source counts toward the 5-source minimum only when it is opened live, is substantive for a plan claim, and is recorded in the Evidence Ledger.

Count these source types toward the external primary minimum:

- official product, framework, platform, or vendor documentation
- API references, SDK references, migration guides, release notes, changelogs, and deprecation notices from the owning project or vendor
- standards, specifications, RFCs, protocol docs, and security advisories from authoritative maintainers or standards bodies
- primary technical references from the project, provider, or maintainer responsible for the behavior being researched

Do not count these toward the external primary minimum:

- repo-local files, tests, docs, issues, or PRs
- Pro/Oracle output, AI answers, search-result pages, snippets, summaries, or copied citations that were not independently opened
- generic blogs, tutorials, Q&A, forum posts, social posts, marketing pages, press, or vendor sales copy
- duplicate mirrors, archived copies, or repeated pages from the same source that do not add a distinct claim
- sources that are stale, version-mismatched, or not current enough for the claim being supported

Use `source_family` to group sources by authority family, such as a vendor, standards body, framework project, cloud provider, database project, or security advisory source. Record `source_family_count` in the completion stamp, and avoid satisfying the evidence bar with many pages from one family when the decision depends on cross-provider, cross-layer, or standards-versus-vendor evidence.

For source authority and source conflict handling:

- prefer the owner of the behavior for product, API, SDK, runtime, security, limit, pricing, and migration claims
- prefer standards or specifications for protocol and interoperability claims, then vendor implementation docs for provider-specific behavior
- prefer repo-local evidence only for what this project currently does; it does not outrank current external primary sources on external behavior
- when sources conflict, record the conflict, the source IDs involved, the authority order used, and the reason the selected source is current enough
- do not adopt a conflicted recommendation until the conflict is reconciled or explicitly marked as a residual risk

Follow-up passes count only when they resolve a source conflict, verify a version or provider constraint, validate a limit, failure mode, rollout, rollback, or recovery concern, test a recommendation against an alternative, or prove an expected bucket is not applicable.

## Research buckets

Cover all applicable buckets below, not just the easiest one:

- core technical approach and architecture patterns
- APIs, interfaces, schemas, storage, or SDK constraints
- limits, quotas, performance, concurrency, or cost constraints
- migration, rollout, rollback, backfill, or recovery behavior
- security, privacy, secrets, auth, or operational readiness
- testing, verification, observability, and failure handling

## Evidence Ledger

The working memo must include an Evidence Ledger. Each source row must include:

- `source_id`
- `source_type`
- `source_family`
- `url`
- `publication_date`
- `last_updated_date`
- `accessed_date`
- `version_or_scope`
- `supported_claims`
- `counts_toward_external_primary_minimum`
- `current_enough_reason`

Use `unknown` for unavailable publication or update dates, but still explain why the source is current enough for each supported claim.

## Draft-Linked Research Agenda

The working memo must include a Draft-Linked Research Agenda before research begins. Each question must name the draft assumption, PRD section, TDD section, `FR-*`, or `TDR-*` it could change, plus the research bucket and possible impact on PRD, TDD, rollout, verification, or task sequencing.

Do not include generic research questions that cannot plausibly change the plan.

## Finding-to-Artifact Delta

The working memo must include a Finding-to-Artifact Delta. Each finding row must include:

- `finding_id`
- `research_question_id`
- `bucket`
- `disposition`
- `recommendation`
- `recommendation_level`
- `support_type`
- `source_ids`
- `prd_tdd_sections_changed`
- `task_plan_inputs_created`
- `disposition_reason`

Use `disposition` values such as `adopted`, `rejected`, or `deferred`. A finding is not adopted unless it changes PRD/TDD or creates an explicit task-plan input; otherwise record the reason in `disposition_reason`.

## Deep Research Completion Stamp

The working memo must end with a Deep Research Completion Stamp containing:

- `external_primary_sources_count`
- `source_family_count`
- `research_questions_answered`
- `buckets_reviewed`
- `follow_up_passes_completed`
- `adopted_findings_count`
- `rejected_or_deferred_findings_count`
- `prd_tdd_sections_changed`
- `task_plan_inputs_created`
- `evidence_bar_met`

Set `evidence_bar_met: yes` only when the minimum evidence bar, Evidence Ledger, Draft-Linked Research Agenda, Finding-to-Artifact Delta, and PRD/TDD revisions are complete. `evidence_bar_met: no` is a planning stop: do not generate `tasks-plan`, do not treat PRD/TDD as final, and report the unmet evidence checks.

## Working memo contract

The temporary research memo must contain:

- web research status
- exact current date used for the research pass, and timezone when known
- project context snapshot for the plan-specific stack and constraints
- version-first stack discovery notes and any unknown versions
- external-query privacy notes, including any redactions or query constraints used
- Evidence Ledger with the required source fields and count eligibility
- Draft-Linked Research Agenda with plan-changing draft links for each question
- Finding-to-Artifact Delta with the required finding, disposition, support, source, artifact-change, and task-input fields
- Deep Research Completion Stamp with counts and `evidence_bar_met`
- external primary sources reviewed, with direct links and one-line notes on what each source answered
- source freshness notes for each substantive external source
- source-family count and source authority notes
- source conflict notes and reconciliation status when sources disagree
- research agenda
- sources reviewed
- improvement backlog and candidate ideas being tested
- findings by bucket
- findings grouped into standards, adopt-now best practices, emerging trends, and outdated advice when applicable
- adopted ideas, rejected ideas, and why
- design decisions or defaults changed by research
- recommendation level for meaningful findings: `adopt now`, `consider`, or `avoid`
- decision checklist or implementation review checklist
- risks or unknowns that remain
- which findings came from external web sources versus repo-local sources
- explicit labels for sourced conclusions versus synthesis versus inference
- explicit note when a bucket was not applicable

Do not start `tasks-plan` drafting until this memo is substantively complete and the adopted findings have been written back into PRD/TDD.

## Research output

Capture these outcomes:

- a short research summary
- concrete recommendations adopted into the plan
- alternatives considered and rejected when they materially affect the design
- the best ideas pulled from the working memo and how they changed PRD/TDD
- risks, constraints, or follow-up validation uncovered by research
- source links or citations supporting the adopted recommendations
- at least 3 answered research questions backed by cited external sources
- a short adopt-now checklist for implementation or review

Default behavior:

- inline the findings into PRD when product-facing constraints changed, into TDD for technical rationale, and into the improve-plan pass
- delete the standalone research memo after planning completes

Preservation behavior:

- if `--preserve-planning-artifacts` is present, keep `tasks/tmp/research-plan-<plan-key>.md`
- mention the preserved artifact path in the final planning summary

## Document boundary rules

- PRD: update only when research changes product-facing constraints, defaults, guardrails, or acceptance behavior
- TDD: absorb the detailed technical recommendations and rationale
- tasks-plan: generate only after PRD/TDD revisions are complete, and add any new rollout, migration, verification, cleanup, or sequencing work discovered by research

## Completion checks

Before continuing to tasks-plan generation:

1. The research has answered the most important technical and delivery questions for this plan.
2. The selected approach is supported by cited external sources, with repo-local context used only as supplemental grounding.
3. Any new risks or sequencing requirements are reflected in revised PRD/TDD where appropriate and are ready to be carried into tasks-plan.
4. The research did not silently widen scope into broad product discovery.
5. The working memo meets the minimum evidence bar, including the external-source minimum and required web-status sections.
6. The Deep Research Completion Stamp says `evidence_bar_met: yes`.
7. `tasks-plan` drafting has not started before the research memo was completed and PRD/TDD revisions were applied.
