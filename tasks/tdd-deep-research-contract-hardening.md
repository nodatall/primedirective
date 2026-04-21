# Deep Research Contract Hardening TDD

## Plain-Language Summary

Prime Directive already has a `--deep-research` planning mode, but it can still be faked with a pile of links and a memo that does not prove the plan actually improved. This work makes the research pass harder to satisfy cosmetically and easier for later agents to audit.

The improved workflow will require research to show what sources counted, what claims those sources supported, what findings changed the PRD or TDD, and what must carry into task sequencing. It will also make sure later Pro analysis and plan refinement cannot silently override research-backed decisions.

The result should keep the current flow practical: no new default human approval gate, no broad product-discovery sprawl, and no implementation work hidden inside planning. It should strengthen the existing Tech + Delivery research pass without turning it into a generic research template.

## Technical Summary

This is a documentation-contract hardening change across Prime Directive skill references. The implementation updates Markdown skill instructions so `--deep-research` has structured audit artifacts, stronger source-count semantics, explicit downstream retention, and guardrails for interactions with `--pro-analysis` and `--refine-plan`.

## Scope Alignment to PRD

The PRD asks for stricter deep-research proof without changing public skill names or adding automation. The technical work stays within existing Markdown skill contracts and shared references.

## Current Technical Diagnosis

The central implementation surface is `skills/shared/references/planning/deep-research.md`. It currently has the right sequencing and evidence intent, but its memo contract is section-heavy and not ledger-driven.

Planning orchestration lives in:

- `skills/plan-work/SKILL.md`
- `skills/plan-and-execute/SKILL.md`
- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/planning/generate-tasks.md`
- `skills/shared/references/planning/improve-plan.md`
- `skills/shared/references/planning/create-tdd.md`
- `skills/plan-refine/SKILL.md`

Validation surface:

- README documents installer smoke checks.
- `.github/workflows/validate.yml` runs `python3 scripts/alfred-skill-router.py --format list` and validates Codex installer idempotence. It does not currently run the Claude installer, so Claude installer validation remains a local smoke check unless this plan explicitly updates CI.
- There is no repo-wide Markdown linter or automated contract parser.

## Architecture / Approach

Update the existing Markdown contracts in place. The approach is to add small, explicit subsections and rules rather than a new skill, script, or artifact type.

The deep-research memo remains `tasks/tmp/research-plan-<plan-key>.md`, but its required content becomes more structured:

- research header
- draft-linked research agenda
- evidence ledger
- finding-to-artifact delta
- completion stamp

Existing memo sections that remain useful can stay, but ledgers become the audit backbone.

## System Boundaries / Source of Truth

Source of truth remains the canonical `skills/` tree in this repository.

`deep-research.md` owns the core research contract. Other files should reference or audit that contract without duplicating all details.

`task-file-contract.md` owns cross-skill modifier and artifact lifecycle behavior.

`plan-and-execute/SKILL.md` owns orchestration order for combined modifiers.

## Dependencies

No new runtime dependencies.

No new external services.

The behavior depends on agent compliance with Markdown instructions and downstream review/refinement prompts reading the relevant artifacts.

## Route / API / Public Interface Changes

No software routes or APIs change.

Public skill modifier names remain unchanged:

- `$plan-work --deep-research`
- `$plan-and-execute --deep-research`
- `$plan-and-execute --pro-analysis`
- `$plan-and-execute --refine-plan`

## Data Model / Schema / Storage Changes

No application data model changes.

Temporary planning memo shape changes inside `tasks/tmp/research-plan-<plan-key>.md` by requiring structured ledger sections. This is a contract change, not a persisted schema with parser support.

## Technical Requirements (`TDR-*`)

- `TDR-001`: `deep-research.md` must define an evidence ledger with required fields `source_id`, `source_type`, `source_family`, `url`, `publication_date`, `last_updated_date`, `accessed_date`, `version_or_scope`, `supported_claims`, `counts_toward_external_primary_minimum`, and `current_enough_reason`, plus source-count rules that distinguish external primary sources from secondary, repo-local, AI-generated, or decorative sources.
- `TDR-002`: `deep-research.md` must require draft-linked research questions and restrict research questions to ones that can affect PRD, TDD, rollout, verification, or task sequencing.
- `TDR-003`: `deep-research.md` must require a finding-to-artifact delta ledger with fields `finding_id`, `research_question_id`, `bucket`, `disposition`, `recommendation`, `recommendation_level`, `support_type`, `source_ids`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `disposition_reason`.
- `TDR-004`: `deep-research.md` must require a completion stamp before tasks-plan generation with fields `external_primary_sources_count`, `source_family_count`, `research_questions_answered`, `buckets_reviewed`, `follow_up_passes_completed`, `adopted_findings_count`, `rejected_or_deferred_findings_count`, `prd_tdd_sections_changed`, `task_plan_inputs_created`, and `evidence_bar_met`, and must define `evidence_bar_met: no` as a planning stop.
- `TDR-005`: `deep-research.md` must define stricter follow-up pass semantics, source conflict authority order, version-first stack discovery, and privacy constraints for external research.
- `TDR-006`: `plan-work/SKILL.md` must pass the research memo into `improve-plan.md` whenever `--deep-research` was used and defer cleanup until planning audits complete.
- `TDR-007`: `create-tdd.md` must require compact durable research-backed rationale in existing TDD sections for adopted technical recommendations.
- `TDR-008`: `generate-tasks.md` must require completion-stamp verification, stop when `evidence_bar_met: no`, and require task coverage for adopted implementation-impact research findings.
- `TDR-009`: `improve-plan.md` must audit evidence ledger, completion stamp, artifact deltas, research memo availability, and stop rather than improve around a failed `evidence_bar_met: no` stamp.
- `TDR-010`: `plan-and-execute/SKILL.md` and `task-file-contract.md` must define combined `--deep-research --pro-analysis` order, Pro reconciliation rules, and a requirement that Pro-suggested sources influence source-backed claims only after independent main-agent verification and Evidence Ledger recording.
- `TDR-011`: `plan-refine/SKILL.md` and `task-file-contract.md` must require refinement to preserve, supersede with reason, or explicitly defer research-backed decisions, and to stop when the deep-research completion stamp says `evidence_bar_met: no`.
- `TDR-012`: Existing local order edits in `plan-and-execute/SKILL.md` and `task-file-contract.md` must be preserved and reconciled with the new rules.

## Ingestion / Backfill / Migration / Rollout Plan

No data migration.

Rollout is a repository instruction update. After implementation, run installer smoke checks. If the user wants global Codex/Claude installs refreshed, they can run the installer in their real environment; this task should validate with temp home smoke checks.

## Failure Modes / Recovery / Rollback

- Overly verbose contract: mitigate by using concise ledgers and not duplicating every detail in every downstream file.
- Contradictory sequencing: mitigate by checking all references for stale “Pro first” or memo cleanup wording.
- Refine-plan bypass: mitigate by adding explicit research carry-forward rules.
- Temporary memo deleted too early: mitigate by changing cleanup timing in `plan-work` and task-file contract.

Rollback is a normal Git revert of Markdown-only changes.

## Operational Readiness

No runtime operations change.

The main operational concern is skill visibility after install. Installer smoke checks should run in temporary homes:

- `HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh`
- `HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`

## Verification and Test Strategy

Focused checks:

- `git diff --check`
- `python3 scripts/alfred-skill-router.py --format list`
- `HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh`
- `HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`

Review checks:

- Search for stale wording such as `Pro analysis first`, `tasks-plan sequencing`, and `research memo when preserved`.
- Confirm no public modifier names changed.
- Confirm planning artifact archive happens after completion.
