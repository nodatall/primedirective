# Rewrite Deliver In Plain Language

Goal: Make the Deliver skill much easier for people and agents to understand while preserving its behavior except for removals the user explicitly approves during wording review.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## Context

- Exact baseline: the Deliver contract package at commit `021ac29`.
- This is a wording and structure rewrite. Preserve existing behavior except for the user-approved removal of draft-discussion mode and its legacy `$deliver discuss` alias.
- The rewrite may shorten `skills/deliver/SKILL.md` by removing repetition and moving conditional detail into the Deliver references that already own it.
- The existing v11 result remains preserved. The new comparison uses fresh baseline and candidate runs; it does not reuse v11 outputs.
- Use fresh `gpt-5.6-sol` agents at `xhigh` reasoning for refinement, both eval arms, and all judges.

## Steps

### 1. Freeze what Deliver means today

- [x] Record each distinct observable decision or obligation from the baseline Deliver skill and its required references once under one canonical behavior ID, including activation, mode order, branch handling, planning, implementation, test value, verification, review scope, stop conditions, archiving, and finalization. List repeated clauses and mirrors as locations under that ID rather than creating duplicate IDs.
- [x] Create a public baseline contract inventory containing each behavior ID, its current owner clause, and a plain behavior summary. The rewrite worker may use this inventory.
- [x] Freeze the exact baseline package from `021ac29`, including every Deliver-owned file and shared reference that an eval scenario must load.
- [x] Create the hidden oracle in a separate evaluator checkout that is not readable from the candidate, rewrite-worker, or canary workspaces. Enforce and test the read denial before candidate work starts. Give those workers only the public inventory; preserve raw cases, expected answers, scoring guidance, and judge guidance only in evaluator-owned artifacts.
- [x] Author, review, and freeze the hidden oracle through evaluator-only agents or processes whose context is never inherited by the Deliver orchestrator, rewrite worker, candidate agents, or canaries. The orchestrator receives only behavior IDs, counts, digests, and a sanitized readiness result. After the candidate is committed, the trusted evaluator may inject official prompts into each arm, but raw answers, scoring guidance, outputs, and judge packets remain evaluator-owned and unreadable from candidate-facing contexts.

### 2. Freeze the before-and-after eval

- [x] Build a thin v12 controller and leave every tracked v11 evaluator file byte-identical. Use `$skill-review` only for exact package extraction, the public state document, and fresh arm and judge allocation. For both behavior scenarios, compose the unchanged v11 per-arm preflight, preparation, two-phase runner, pre-packet freeze, packet staging, arm finalization, and normalization controls as read-only dependencies. Bind the exact `021ac29` baseline and approved candidate package manifests, fixed arm order, one-shot attempt and restart policy, sealed outputs, and failure transitions before the first arm starts. Do not replay these scenarios through generic shadow-run prompts alone.
- [x] Do not use v11's official comparison manifest, blind-packet, gate, or final-verdict path; those controls are frozen to the old refs, package lists, and strict cost-improvement policy. Add only a separately owned adapter for the new bindings, comprehension fixtures and schemas, hidden-case orchestration, grouping both behavior scenarios by arm, non-regression gate, three blind judges, and combined verdict. The adapter may call unchanged v11 per-arm controls but must not copy or reimplement their staging, sandbox, freeze, or normalization logic. If those controls cannot be composed, stop and revise the plan rather than accept weaker evidence.
- [x] Use at least twelve realistic comprehension cases covering the named Deliver decisions. Let one case cover several compatible canonical behavior IDs, and add only the minimum further cases needed to close uncovered comprehension behavior.
- [x] Require each arm to return the same small structured answer for every case: next action, required artifact, required check, stop condition, and whether user approval is needed.
- [x] Use a frozen typed vocabulary or atomic answer sets for hard-scored fields. Keep optional prose rationale out of deterministic scoring and discard it before blind judge packets; do not use exact generated wording or regular-expression matches as correctness evidence.
- [x] Reuse the Queuectl and historical preflight scenarios as the full behavior lane. Preserve their correctness checks and exact expected test and rereview categories, but require non-regression rather than another strict cost improvement from a wording-only rewrite. Run the existing hidden checks only from the evaluator against sealed arm state, bind every result to that arm's seal digest, and never stage the ledger or hidden checks into runner inputs, judge packets, or the public state document.
- [x] Freeze the scenarios, behavior inventory, hidden answers, rubrics, model and reasoning settings, time limits, allowed tools, stop boundaries, scoring rules, and failure transitions before editing the candidate skill.
- [x] Freeze a behavior-to-evidence matrix before editing the candidate. Every behavior ID must map to a hidden deterministic comprehension assertion, a full behavior-lane gate, or a static ownership-and-routing check. An uncovered behavior ID fails the comparison.
- [x] Allow a static ownership-and-routing check to satisfy a behavior ID only when it mechanically proves that the canonical owner is byte-identical across packages and routed before the affected decision, or when it checks an immutable machine token or enum exactly. Every behavior whose owning prose changes must instead have a hidden deterministic comprehension assertion or a full behavior-lane gate. The candidate-authored behavior map is audit metadata, not pass evidence.
- [x] Create or refresh the normal `$skill-review` state document before shadow runs. Record the baseline, evaluator version, scenario, preserved artifact root, package identities as they become available, and each frozen verdict transition. The three frozen v12 judge lanes replace `$skill-review`'s ordinary post-pairwise judge step. No judge receives arm identity or the changed diff before its verdict is frozen, and the completion stamp summarizes the combined v12 verdict.
- [x] Run a fresh adversarial evaluator review and commit the frozen evaluator before candidate work starts. Any later change to the evaluator, oracle, rubric, behavior matrix, scoring, or failure policy invalidates that comparison version and requires a new version with fresh disjoint hidden cases and judges, even when no official arm has started.

### 3. Rewrite the full Deliver contract

- [x] Rewrite `skills/deliver/SKILL.md` as a short plain-language entry point that keeps the purpose, modes, artifacts, workflow order, approval boundaries, stop rules, and reference routing.
- [x] Rewrite the Deliver-owned plan, worker-packet, and rereview-scope references in plain language where they remain necessary; remove duplicate wording instead of moving the same repetition between files.
- [x] Keep all command names, paths, enum values, schema versions, modifiers, completion-stamp fields, and other machine-facing tokens unchanged. Wording-only edits may update validator mirrors, but must not change the underlying token or accepted behavior.
- [x] Follow the skill-creator metadata contract and read its `openai_yaml` reference before editing `skills/deliver/agents/openai.yaml`. Preserve invocation policy and unrelated fields; change only interface wording and required behavior-equivalent validator mirrors. Include the file in candidate and readability packages.
- [x] Using only the public contract inventory, map every retained baseline behavior ID to one clear candidate clause or an unchanged owner reference that Deliver routes to before the first affected decision. Record user-approved removals separately. Reject any other missing, duplicated, conflicting, or expanded behavior.
- [x] Treat shorter word count and fewer long sentences as useful measurements, not hard targets. Prefer the simplest correct wording over a forced line limit.
- [x] Run validation and independent forward checks using canaries that are not part of the official comparison. Do not expose official case prompts, hidden answers, judge feedback, or official results before candidate freeze.
- [x] Pause for the user's wording review. The user approved the wording on 2026-09-10 after removing draft-discussion mode and its legacy alias. The updated behavior map, validation, and disjoint canary all passed before candidate freeze at `23b3d4e`.

### 3.5. Re-freeze the comparison for the approved removal

- [x] After wording approval, create a new evaluator version with fresh hidden cases and fresh judges. V12.30 is author-ready with the five public draft-only behavior IDs treated as approved removals and hard non-regression preserved for every retained behavior; independent review and trusted-host isolation remain pending.
- [ ] Repeat independent evaluator review and trusted-host isolation before running either official arm. Do not reuse the frozen v12.22 result as the final comparison.

### 4. Run the frozen comparison

- [ ] Commit and extract the exact approved candidate package, then run fresh baseline and candidate comprehension arms on identical hidden cases with isolated inputs and preserved artifacts.
- [ ] Require the candidate to pass every frozen comprehension assertion. Preserve baseline assertion results as the comparator: a baseline miss is valid comprehension evidence, not an invalid arm. The candidate may not regress any assertion the baseline passed or any static or full-behavior gate.
- [ ] Give the blinded comprehension outputs to a fresh outputs-only judge. Give anonymized copies of the exact contract packages each arm loaded, including routed references, to a separate fresh readability judge. Correctness remains a hard gate, and a shorter `SKILL.md` alone is not evidence of clearer effective instructions.
- [ ] Run fresh baseline and candidate behavior arms on both existing implementation scenarios with identical inputs, tools, limits, and stop boundaries.
- [ ] Require material correctness, all frozen test dispositions, all frozen rereview scopes, and existing safety gates to pass. Require no regression on the frozen deterministic structural measures, including test disposition, rereview scope and rounds, permanent test size, and required ceremony. Treat wall time and token use as diagnostic unless the evaluator freezes a justified tolerance before candidate editing.
- [ ] Give the blinded behavior artifacts to a separate fresh judge. Accept `candidate_better` or `candidate_neutral` only when no deterministic behavior gate regresses.
- [ ] Publish one combined verdict. Pass only when the outputs-only comprehension judge returns `candidate_better`, the contract readability judge returns `candidate_better`, the behavior judge returns `candidate_better` or `candidate_neutral`, the user explicitly approves the wording, and every deterministic gate passes. Freeze every judge verdict before identity reveal; `inconclusive` does not pass.
- [ ] If any official gate fails, preserve the evidence and stop. Do not edit the frozen evaluator or tune and rerun the same version. Any revision starts a new versioned comparison with fresh disjoint hidden comprehension cases and new judges. Retire failed official comprehension cases to diagnostic-only; reuse the fixed public behavior scenarios only for regression parity.

### 5. Validate and close out

- [ ] Complete the public skill-review summary and completion stamp without copying hidden or answer-revealing material into it.
- [ ] Run the full Deliver and evaluator test suites, skill-contract validation, quick skill validation, plugin installation, and diff checks.
- [ ] Run a fresh full-branch review of that exact state. Rerun affected validation after every repair. If a repair changes the evaluated contract package or any evaluator input, control, or gate, invalidate the verdict and run a newly versioned complete comparison before closeout.
- [ ] Archive this execution plan and commit only the intended rewrite, eval, validation, and closeout files. Then complete the Deliver finalization gate outside the checklist.
