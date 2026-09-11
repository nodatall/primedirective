# Deliver Skill Review: Plain-Language Rewrite V12

Invocation: `$skill-review skill=deliver scenario=deliver-plain-language-v12 baseline=021ac29 --preserve-review-artifacts`

- Skill: `deliver`
- Baseline: `021ac29eab5b28afc2222e16944c540dfd8362e9`
- Candidate: `23b3d4e38b30f882c4a6f20f293b73f701138e3b`
- Evaluator version: `deliver-plain-language-v12.32` (controller frozen; independent bundle pending)
- Public adapter: `deliver_plain_language_v12` at `evals/deliver/plain-language-v12/adapter.py`
- Public process policy: `evals/deliver/plain-language-v12/execution-policy.json`
- Scenario: frozen comprehension packet plus unchanged `retry-failed` and `preflight-remediation-holdout` behavior lanes
- Runner: bundled Codex, `gpt-5.6-sol`, `xhigh`
- Preserved artifact root: `agent-scratch/skill-review/deliver-plain-language-v12/`
- Verdict: pending official arms and three frozen v12 judge lanes
- Merge readiness: blocked until the complete v12 comparison finishes

## Frozen Public Identities

- Baseline package source commit: `021ac29eab5b28afc2222e16944c540dfd8362e9`
- Baseline package authority digest: `755d7c7db5f88bd2f3a21c5bf9adcc9c357c13188a207f4c6461b2cb32fb18e5`
- V11 immutable content-manifest digest: `fc3cb2d9311a9f1def033f582c10a6a0af45fed9fc4cdcbda37dadcffef7b9b2`
- Candidate package commit: `23b3d4e38b30f882c4a6f20f293b73f701138e3b`
- Candidate package authority digest: `c3330c9405f3635027ce82965c1743a988686cc81336468733b7ee0411d9d7ae`
- Retained public behaviors: 103
- User-approved removed public behaviors: 5
- Invalidated evaluator: `deliver-plain-language-v12.23`; rejected because its combine step accepted unbound lane-verdict objects.
- Invalidated evaluator: `deliver-plain-language-v12.24`; rejected because caller-provided roots and pass booleans could authenticate themselves and aggregation could downgrade regression to neutral.
- Invalidated evaluator: `deliver-plain-language-v12.25`; rejected because packet freezing accepted caller-authored lane payloads and attached verified provenance without deriving those bytes from sealed-arm artifacts.
- Invalidated evaluator: `deliver-plain-language-v12.26`; rejected because its author-ready bytes could not make the required committed review and isolation transitions, and several control counts were declarations rather than executed named-control totals.
- Invalidated evaluator: `deliver-plain-language-v12.27`; rejected because a nested comprehension payload field exposed literal arm identity while its published blinding control inspected only the outer provenance field.
- Invalidated evaluator: `deliver-plain-language-v12.28`; rejected because its recursive value denylist treated authenticated contract prose as control metadata and rejected legitimate package content.
- Invalidated evaluator: `deliver-plain-language-v12.29`; rejected because its root-isolation wrapper accepted self-asserted pass environment variables and falsely claimed a network boundary that the host does not provide.
- Invalidated evaluator: `deliver-plain-language-v12.30`; rejected because its frozen root-isolation closure omitted the dynamically imported Deliver harness, allowing a descendant harness replacement to fabricate a passing probe.
- Invalidated evaluator: `deliver-plain-language-v12.31`; rejected because one independently authored bundle file was replaced during import while the original manifest remained, so standalone and integrated bindings could not both be true.
- V12.32 Phase A freezes the public schema and complete eight-file independent-bundle interface before hidden case authoring. The controller binds every public code/data input used by the readiness, isolation, and bundle-validation paths. Imported bundle files, including the manifest, must remain byte-identical; no build step may rewrite them.
- V12.32 hidden case authoring, private evaluator source/final commits, author readiness, independent review, trusted-host isolation, official arms, and judge runs are all pending.
- Committed wording-approval record: `9d8f98f34cb6ebfe78f067be832f4c2c41f00ce5`
- Official runtime, run ID, nonce, run-label-map digest, and arm seals: created only by `initialize` after public and private readiness gates pass

## Public Controller Status

- [x] Public adapter identifier and exact operation surface defined.
- [x] Frozen Sol/xhigh process, polling, cumulative arm-total timeout, one-shot, restart, and reattachment policy defined and enforced through sealing.
- [x] Exact package, Git source, runtime filesystem, packet, schema, evaluator, and policy binding implemented.
- [x] Unchanged v11 preparation, runner, pre-packet freeze, packet staging, finalization, and normalization controls composed.
- [x] Canonical per-arm artifact sealing and deterministic write-once handoff implemented.
- [ ] Import and validate a fresh independent v12.32 bundle, then freeze the private evaluator and author-ready state.
- [x] Approved candidate package is committed and bound to its exact public manifest.
- [ ] Fresh baseline and candidate arms complete with comparable inputs.
- [ ] Outputs-only comprehension, contract-readability, and behavior judge verdicts freeze before identity reveal.
- [ ] Combined v12 verdict and user wording approval are recorded.

## Controller Freeze

Phase A ends at `controller_frozen_awaiting_independent_bundle`. This state is
not `author_ready` and cannot initialize an official run. The next author phase
must import all eight source files byte-for-byte from one committed independent
bundle, reconcile standalone and integrated validation against this exact
controller, and only then create the private source/final and `author_ready`
state. The later readiness order remains `author_ready` ->
`independent_review_pass` -> `ready`.

```bash
python3 evals/deliver/plain-language-v12/readiness_transition.py verify-controller-frozen --repo . --ref HEAD
```

## Frozen Verdict Transitions

- Evaluator, integrity, comparability, or ambiguous failure: `inconclusive`; stop without tuning or replaying v12.
- Candidate terminal or deterministic non-regression failure: `candidate_regression`; preserve evidence and stop.
- Correctness passes but the required benefit gates do not: `candidate_neutral` or `inconclusive`, as established by the frozen combined gate; do not merge from v12.
- All deterministic gates pass, both required clarity judges prefer the candidate slot, the behavior judge is neutral or prefers the candidate slot, and the committed wording approval remains valid: `candidate_better`; proceed to normal merge review.
- Only one infrastructure restart is permitted, and only before any output. A semantic retry is never permitted.

This public state contains no comprehension prompts, expected answers, option mappings, scoring guidance, identity mapping, or judge rubric.

## Skill Review Completion Stamp

skill_review_complete: no
skill_name: deliver
state_doc: tasks/skill-review-deliver-plain-language-v12.md
baseline_ref: 021ac29eab5b28afc2222e16944c540dfd8362e9
candidate_ref: 23b3d4e38b30f882c4a6f20f293b73f701138e3b
scenario: deliver-plain-language-v12
baseline_run_complete: no
candidate_run_complete: no
comparable_inputs: no
judge_run_complete: no
judge_blinded: no
verdict: inconclusive
artifact_evidence_preserved: no
ready_for_merge_review: no
stop_reason: missing_judge
