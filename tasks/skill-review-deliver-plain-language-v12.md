# Deliver Skill Review: Plain-Language Rewrite V12

Invocation: `$skill-review skill=deliver scenario=deliver-plain-language-v12 baseline=021ac29 --preserve-review-artifacts`

- Skill: `deliver`
- Baseline: `021ac29eab5b28afc2222e16944c540dfd8362e9`
- Candidate: `23b3d4e38b30f882c4a6f20f293b73f701138e3b`
- Evaluator version: `deliver-plain-language-v12.28`
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
- V12.28 constructs exact lane-specific judge projections at the private boundary, keeps scores, roots, seals, and identity maps private, and recursively rejects identity-bearing keys and string values before freezing any judge packet.
- Evaluator source and author-ready commits: `279e023e8c14e9497d5c3a2d0b35959dc16acf3e` and `f2fbcf6bed807d224e5d4e8cd10e97cd1b3d0a47`
- Public controller commit: `b542538d36d87961dc6468b503514eee8df4c35a`
- Public author-ready commit: `c20ab349094d28c76c6f41d321a9fffdf6826900`
- Author-ready-state SHA-256: `3855fcbc17d121b0d16bb71f4c3dcad86d287d9fd11ec632d55b36f501291975`
- Committed wording-approval record: `9d8f98f34cb6ebfe78f067be832f4c2c41f00ce5`
- Official runtime, run ID, nonce, run-label-map digest, and arm seals: created only by `initialize` after public and private readiness gates pass

## Public Controller Status

- [x] Public adapter identifier and exact operation surface defined.
- [x] Frozen Sol/xhigh process, polling, cumulative arm-total timeout, one-shot, restart, and reattachment policy defined and enforced through sealing.
- [x] Exact package, Git source, runtime filesystem, packet, schema, evaluator, and policy binding implemented.
- [x] Unchanged v11 preparation, runner, pre-packet freeze, packet staging, finalization, and normalization controls composed.
- [x] Canonical per-arm artifact sealing and deterministic write-once handoff implemented.
- [x] Private evaluator reaches its author-ready state with sealed-artifact-derived packets, verified trust roots, recomputed hard gates, exact lane schemas, and a write-once comparison lifecycle; independent review and trusted-host isolation remain pending.
- [x] Approved candidate package is committed and bound to its exact public manifest.
- [ ] Fresh baseline and candidate arms complete with comparable inputs.
- [ ] Outputs-only comprehension, contract-readability, and behavior judge verdicts freeze before identity reveal.
- [ ] Combined v12 verdict and user wording approval are recorded.

## Readiness Transitions

The committed readiness state advances only in this order: `author_ready` ->
`independent_review_pass` -> `ready`. The transition helper verifies immutable
evaluator identities, exact frozen public file bytes and last-touch commits,
the predecessor commit and digest, and the stage-specific record before it
prepares the next state. Each prepared transition must be committed as exactly
the two allowlisted files before the matching verify command succeeds.

```bash
python3 evals/deliver/plain-language-v12/readiness_transition.py verify-author-ready --repo . --ref HEAD
python3 evals/deliver/plain-language-v12/readiness_transition.py prepare-independent-review --repo . --record /absolute/path/to/v12.28-independent-review-record.json
git add evals/deliver/plain-language-v12/oracle-readiness.json evals/deliver/plain-language-v12/independent-review-record.json
git commit -m "Record Deliver evaluator v12.28 independent review"
python3 evals/deliver/plain-language-v12/readiness_transition.py verify-independent-review --repo . --ref HEAD
python3 evals/deliver/plain-language-v12/readiness_transition.py prepare-ready --repo . --receipt /absolute/path/to/v12.28-trusted-host-isolation-receipt.json
git add evals/deliver/plain-language-v12/oracle-readiness.json evals/deliver/plain-language-v12/trusted-host-isolation-receipt.json
git commit -m "Mark Deliver evaluator v12.28 ready"
python3 evals/deliver/plain-language-v12/readiness_transition.py verify-ready --repo . --ref HEAD
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
