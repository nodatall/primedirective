# Deliver Regression Eval Suite

This tracked suite compares two versions of the `$deliver` contract through the existing `$skill-review` workflow. It does not add an orchestration layer. The suite freezes two scenarios, evaluator outcomes, runner isolation, staged review packets, normalization, and the blinded judge contract.

## Required invocation

Run from the Prime Directive repository with fresh `gpt-5.6-sol` runners at `xhigh` reasoning:

```text
$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=<ref> candidate=<ref-or-worktree> --preserve-review-artifacts
```

`$skill-review` owns baseline/candidate reconstruction, fresh runner and judge allocation, the durable state document, and preserved scratch root. This suite supplies the realistic scenarios and deterministic gates. Use the same runner model, reasoning, tools, approval, and local-only stop boundary for both arms. Do not use native Plan mode or Pro analysis in this required regression lane.

## Frozen scenarios

1. [`retry-failed`](retry-failed/scenario.json) is the original Queuectl known case. The clean fixture preserves the pilot's semantic contents with only trailing blank EOF lines normalized, then freezes that normalized tree and every fixture-file hash. Its three public tests, source bullets, acceptance contract, fixed approval, and original seven hidden checks remain the pilot cases. Its eleven later reviewer-derived checks are unchanged diagnostic post-hoc challenges, not unbiased acceptance checks.
2. [`preflight-remediation-holdout`](preflight-remediation-holdout/scenario.json) replays the already-approved May 30 remediation at exact commit `27103d3a05eb20072d29917532326a5cbd59dc8f`. Its packet contains the corrupt-throttle and asynchronous-preflight findings, deterministic versions of the original probes, the paused plan, and the behavior later fixed in `2e0c01916bebceca619f1b209a101e591ebfd07d`.

The evaluator-owned [`outcome-ledger.json`](evaluator/outcome-ledger.json) is frozen before contract edits. It is not supplied to either runner. It spans all four test dispositions and both rereview scopes.

## Staged protocol

For each scenario and each arm:

1. Extract only that arm's Deliver contract and required references through `$skill-review` into one package directory. Preserve their package-relative paths.
2. Prepare an empty stage. This builds a fresh deterministic git snapshot and a hash-allowlisted input manifest:

   ```bash
   python3 evals/deliver/harness.py prepare --scenario retry-failed --contract <extracted-contract-package> --destination <arm-stage>
   python3 evals/deliver/harness.py verify-manifest <arm-stage>
   ```

3. Give the runner only `<arm-stage>/repo`, `<arm-stage>/scenario`, `<arm-stage>/contract`, the fixed approval, and the local stop boundary. Save its recorded JSONL tool trace. Never expose any path under `evals/deliver/**/evaluator`, `evals/deliver/evaluator`, or a ledger path.
4. Before providing the review packet, freeze the actual starting or pre-packet implementation state, diff, and validation evidence:

   ```bash
   python3 evals/deliver/harness.py freeze-pre-packet <arm-stage> --validation <public-validation-log>
   python3 evals/deliver/harness.py stage-review-packet <arm-stage>
   ```

5. Run remediation under the extracted contract. Record post-remediation code, tests, one-run probes, review logs, public validation, review-round counts, and start/end timing, then freeze before evaluator access:

   ```bash
   python3 evals/deliver/harness.py freeze-output <arm-stage> --record <run-record.json> --trace <runner-trace.jsonl>
   ```

   This hashes the actual implementation and test diffs, record, and pre-freeze trace, writes `evidence/output-freeze.json`, and appends the trace freeze marker.
6. Audit the trace before copying hidden tests, challenge probes, the ledger, or judge inputs into evaluator-owned scratch:

   ```bash
   python3 evals/deliver/harness.py audit-trace <runner-trace.jsonl>
   ```

7. Run the original hidden checks and historical probes unchanged. Run post-hoc Queuectl challenges separately and label their results `diagnostic_posthoc`; they cannot alter acceptance-check totals.
8. Create the evaluator-owned `run-record.json` described below, normalize it, and build the blind pair. Judge behavior first. Reveal workflow identity and run candidate-only contract compliance only after the blinded verdict is frozen.

The packet-staging command refuses to run without `evidence/pre-packet-snapshot.json`. Preparation rejects nonempty destinations, symlinks, escaping paths, evaluator/ledger names, a drifted historical ref/tree, and any unlisted input. Each manifest and every listed file has a SHA-256 digest.

## Run record and normalization

Place `run-record.json` beside its evidence files. Paths are relative, regular, non-symlink files inside that record root:

```json
{
  "scenario_id": "retry-failed",
  "snapshots": {"pre_packet": "<sha256>", "post_remediation": "<sha256>"},
  "evidence": {
    "implementation_diff": "evidence/implementation.diff",
    "test_diff": "evidence/tests.diff",
    "probe_results": "evidence/probes.json",
    "review_log": "evidence/reviews.json"
  },
  "measurements": {
    "test_count": 0,
    "test_size_lines": 0,
    "full_review_rounds": 0,
    "targeted_rereviews": 0,
    "wall_time_seconds": 0
  },
  "identity_clues": ["arm-specific scratch name", "evaluated commit ref"]
}
```

`probe_results` and `review_log` are JSON arrays with stable finding/test IDs, dispositions, scopes, commands, exit statuses, and evidence. The normalizer uses the actual implementation diff, test diff, probes, and review actions; normalizes line endings; redacts paths, commit IDs, declared clues, and the identity denylist; rejects candidate-compliance fields before reveal; and emits [`behavior-schema.json`](evaluator/behavior-schema.json).

```bash
python3 evals/deliver/harness.py normalize <run-record.json> --output <normalized.json>
python3 evals/deliver/harness.py blind-packet <normalized-1.json> <normalized-2.json> --output <blind-packet.json>
```

Blind labeling is assigned by normalized-content digest, so swapping input arm order produces byte-identical Run A/Run B packets. Candidate field compliance is a separate post-reveal artifact and must never appear in `run-record.json`. After reveal, provide only the candidate's structured field report and check it separately:

```bash
python3 evals/deliver/harness.py check-candidate-compliance <candidate-fields.json> --output <candidate-compliance.json>
```

## Evaluator order and evidence

The evaluator freezes, in order: runner outputs; trace audit; acceptance and diagnostic probe results; normalized packets; blinded verdict; identity reveal; candidate compliance; cost measurements; ledger gate; final verdict. Preserve all of them in the `$skill-review` scratch root and summarize them in its durable state document.

The hard ledger gate requires every registered outcome before the qualitative judge can prefer the candidate. The blinded judge uses [`judge-rubric.md`](evaluator/judge-rubric.md): correctness first, then durable test value, consolidation, rereview breadth, test count/size, full rounds, wall time, and ceremony. No hard line-count cap applies.

## Harness checks

```bash
python3 -m unittest discover -s evals/deliver/tests -v
python3 evals/deliver/harness.py validate-ledger
git diff --check
```
