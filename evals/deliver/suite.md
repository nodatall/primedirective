# Deliver Regression Eval Suite v11

This tracked suite compares exact Deliver baseline `a4116bb` with exact candidate `8a489bc` through `$skill-review`. The v11 harness adds a frozen comparison manifest and evaluator-owned attempt state so the existing workflow has one identity, one four-arm order, and one digest chain from preflight through final verdict.

## Required invocation

Run from the Prime Directive repository with fresh `gpt-5.6-sol` runners at `xhigh` reasoning:

```text
$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=<ref> candidate=<ref-or-worktree> --preserve-review-artifacts
```

`$skill-review` owns baseline/candidate reconstruction, fresh runner and judge allocation, the durable state document, and preserved scratch root. This suite supplies the realistic scenarios and deterministic gates. Use the same runner model, reasoning, tools, outer execution boundary, and local-only stop boundary for both arms. Do not use native Plan mode or Pro analysis in this required regression lane.

The v11 execution budget is 90 minutes total across each arm's pre-packet and remediation phases, with a 15-minute inactivity timeout. Inactivity means no structurally valid event from the fixed Codex JSONL event-type allowlist has arrived on runner stdout; unknown, fabricated, malformed, partial, or arbitrary bytes do not extend the deadline. Earlier attempts and completed comparisons remain diagnostic artifacts and are excluded from v11 scoring.

## Frozen scenarios

1. [`retry-failed`](retry-failed/scenario.json) is the original Queuectl known case. The clean fixture preserves the pilot's semantic contents with only trailing blank EOF lines normalized, then freezes that normalized tree and every fixture-file hash. Its three public tests, source bullets, acceptance contract, fixed approval, and original seven hidden checks remain the pilot cases. Its eleven later reviewer-derived checks are unchanged diagnostic post-hoc challenges, not unbiased acceptance checks.
2. [`preflight-remediation-holdout`](preflight-remediation-holdout/scenario.json) replays the already-approved May 30 remediation from the two required scripts at exact commit `27103d3a05eb20072d29917532326a5cbd59dc8f`. The fixture records the source commit, source tree, and exact blob/mode for each script but deliberately does not materialize the rest of that historical repository, so the runner sees only one Deliver contract: the separately extracted arm package. Before packet staging the runner sees only a generic inspection-only starting-state contract. The packet later supplies the corrupt-throttle and asynchronous-preflight findings, deterministic versions of the original probes, the paused plan, and the behavior later fixed in `2e0c01916bebceca619f1b209a101e591ebfd07d`.

The v11 evaluator-owned [`outcome-ledger.json`](evaluator/outcome-ledger.json) is frozen before contract edits. It is not supplied to either runner. It spans all four test dispositions and both rereview scopes.

## Frozen comparison and staged protocol

First extract both exact contract packages. From one clean committed evaluator checkout, initialize a new runtime. This freezes the evaluator commit, `evals/deliver` tree, canonical evaluator-file digest, exact package manifests, the runtime, the external sentinel, and this arm order: retry baseline, retry candidate, holdout baseline, holdout candidate. Later closeout commits may advance `HEAD` only when the frozen evaluator tree and file digest remain byte-identical.

```bash
python3 evals/deliver/harness.py initialize-comparison \
  --runtime-root /private/tmp/deliver-eval-<run> \
  --baseline-package <baseline-package> \
  --candidate-package <candidate-package> \
  --comparison-id <unique-id>
```

The evaluator must be clean, the candidate-owned paths must still equal `8a489bc`, and the evaluator commit may change only the eight v11 allowlisted paths: the harness, its consolidated tests, this suite, and the five evaluator schemas including the shared comparison-artifact definitions. Once arm 1 starts, evaluator editing is closed. The attempt state rejects reordered arms, a second start of a sealed arm, non-monotonic phase changes, and all restarts except one recorded external interruption of the active unsealed phase with byte-identical inputs.

For each scenario and each arm:

1. Preflight the only compatible runner binary. This command never falls back to `PATH` or Homebrew: it resolves `/Applications/ChatGPT.app/Contents/Resources/codex`, records its absolute path, version, executable SHA-256, and the arm timeout policy, and performs a tiny real Sol/xhigh JSONL smoke under the same outer sandbox used for scenarios. The smoke has its own fixed two-minute total and one-minute inactivity limits so preflight stays quick; both policies are validated from the preserved preflight artifact. Preserve that evaluator artifact in the `$skill-review` scratch root:

   ```bash
   python3 evals/deliver/harness.py preflight-runner --comparison-manifest <comparison-manifest.json> --output <runner-preflight.json>
   ```

2. Extract only that arm's Deliver contract and required references through `$skill-review` into one package directory. Preserve their package-relative paths.
3. Prepare an empty stage at `/private/tmp/deliver-eval-<run>/<scenario>-<baseline|candidate>`. The runtime may contain only the four stable arm names, the sibling probe, and evaluator control directory. Preparation re-hashes the selected package against the frozen comparison before building its deterministic snapshot and allowlisted runner manifest:

   ```bash
   python3 evals/deliver/harness.py prepare --scenario retry-failed --contract <extracted-contract-package> --destination <arm-stage> --runner-preflight <runner-preflight.json> --comparison-manifest <comparison-manifest.json>
   python3 evals/deliver/harness.py verify-manifest <arm-stage>
   ```

4. Start the pre-packet runner through the harness. This invokes the preflight-pinned bundled Codex with actual `exec --json --ephemeral --ignore-user-config --strict-config`, fixed `gpt-5.6-sol`/`xhigh`, and `--dangerously-bypass-approvals-and-sandbox`. `/usr/bin/sandbox-exec` is the sole runner boundary. Its profile denies all reads and writes under `/private/tmp`, then narrowly allows the current arm stage; the existing user-home, volume, sibling, empty-environment, authentication-copy, stream-capture, timeout, and process-group protections remain. Before and after every runner, the evaluator requires the fixed-byte external sentinel to exist as a mode-0600 regular file with its frozen digest. The mandatory first tool proves that authentication and inherited state are absent and that both reading and writing that real external sentinel fail. The host integration test also proves `/tmp` alias, relative traversal, and allowed-stage symlink escape failures. Metadata carries the frozen comparison/evaluator binding plus every existing runner and timeout binding.

   ```bash
   python3 evals/deliver/harness.py run-scenario <arm-stage> --phase pre-packet
   ```

   Never expose any path under `evals/deliver/**/evaluator`, `evals/deliver/evaluator`, or a ledger path.
5. Before providing the review packet, freeze the actual pre-packet state and validation evidence. The command requires a completed, verified pre-packet runner bundle, verifies the existing manifest, recomputes `HEAD`, status, and code/test diffs against the initial snapshot, and binds the exact snapshot, runner preflight, and copied validation bytes to that manifest digest. For the historical holdout, evaluator-owned Git reads explicitly disable replacement objects. `HEAD` and the sole `refs/heads/eval` ref must still equal the initial snapshot; grafts, shallow metadata, extra refs, extra Git objects, and reflog object IDs beyond the initial commit are rejected. Both pinned scripts must also retain their evaluator-owned blob and executable-mode values in the `HEAD` tree, Git index, and working tree. This blocks normal retained-history channels after an early repair, including reset, side-ref, replacement-ref, staged, unstaged, deleted, or mode-only drift, while allowing untracked non-source bookkeeping. It does not claim protection from a malicious runner that deletes or rewrites every raw Git trace it created:

   ```bash
   python3 evals/deliver/harness.py freeze-pre-packet <arm-stage> --validation <public-validation-log>
   python3 evals/deliver/harness.py stage-review-packet <arm-stage>
   ```

6. Start remediation through the same fixed runner after packet staging. The packet command first verifies the old manifest and refuses to rehash runner-modified contract or scenario inputs; the new review-packet manifest records the frozen pre-packet manifest as its parent.

   ```bash
   python3 evals/deliver/harness.py run-scenario <arm-stage> --phase remediation
   ```

   Record post-remediation code, tests, structured probes, and review actions, then finalize the arm before evaluator access:

   ```bash
   python3 evals/deliver/harness.py finalize-arm <arm-stage> --record <run-record.json>
   ```

   This is the only arm-finalization path; it accepts no caller-selected trace. It requires both harness-produced runner phases and verifies their exact outer-sandbox commands, phase identities, successful exits, prompt/trace/stderr/profile digests, initial snapshot, manifest lineage, identical timeout policy, cumulative arm budget, evaluator identity, and comparison identity. It writes the frozen output and terminal seal, then registers exactly that seal digest as one atomic transition under the evaluator lock. Duplicate or concurrent seal submissions fail without changing the first binding. Normalization may resume from a registered seal, but the arm itself may never rerun.

   If either deadline expires, the harness sends `SIGKILL` to the isolated runner process group, reaps the leader, removes the arm-local authentication copy, integrity-checks and publishes the already-flushed partial trace and stderr as diagnostics, and raises without writing valid runner metadata. Cleanup repeats the safe process-group stop even when the leader exited first so background descendants cannot survive. The harness refuses to signal its own process group. Without valid metadata, finalization and terminal sealing remain impossible; the timed-out arm is excluded rather than scored.

   Only a verified external interruption before sealing may be recorded and restarted with identical inputs:

   ```bash
   python3 evals/deliver/harness.py record-external-interruption --comparison-manifest <comparison-manifest.json> --arm <arm-name> --phase <pre-packet|remediation> --reason <reason>
   ```

7. Run the original hidden checks and historical probes unchanged. Run post-hoc Queuectl challenges separately and label their results `diagnostic_posthoc`; they cannot alter acceptance-check totals.
8. Normalize each finalized arm and build the blind pair. Judge behavior first. Reveal workflow identity and run candidate-only contract compliance only after the blinded verdict is frozen.

The packet-staging command refuses to run without `evidence/pre-packet-snapshot.json`. Preparation rejects nonempty destinations, symlinks, escaping paths, evaluator/ledger names, multiple or non-Deliver `SKILL.md` files, a drifted historical commit/tree/blob, and any unlisted input. Each manifest and every listed file has a SHA-256 digest.

The threat model separates the trusted evaluator/operator from the untrusted runner. The outer sandbox denies the user home, volumes, and all of `/private/tmp`, then allows only the current arm stage. Thus older eval roots, unrelated temporary data, sibling arms, evaluator state, and the external sentinel remain outside the runner boundary. The empty environment prevents parent token variables from entering it. The sentinel, first-tool gate, trace checks, frozen identities, locked attempt state, and terminal seal are fail-closed lifecycle and audit controls; they are not protection from a trusted operator who can rewrite the evaluator checkout itself.

## Run record and normalization

Place [`run-record.json`](evaluator/run-record-schema.json) beside its evidence files. Paths are relative, regular, non-symlink files inside that record root:

```json
{
  "scenario_id": "retry-failed",
  "evidence": {
    "implementation_diff": "evidence/implementation.diff",
    "test_diff": "evidence/tests.diff",
    "probe_results": "evidence/probes.json",
    "review_log": "evidence/reviews.json",
    "review_rounds": "evidence/review-rounds.json"
  },
  "measurements": {
    "test_count": 1,
    "test_size_lines": 12,
    "full_review_rounds": 0,
    "targeted_rereviews": 3,
    "wall_time_seconds": 42
  },
  "identity_clues": ["arm-specific scratch name", "evaluated commit ref"]
}
```

The numbers above only illustrate the record shape. Use the values derived from that arm's frozen diff, review actions, and runner metadata; `finalize-arm` rejects any mismatch.

`probe_results`, `review_log`, and `review_rounds` follow [`evidence-records-schema.json`](evaluator/evidence-records-schema.json). Each item has a command, exit status, nonblank summary, and `evidence_ref`/`evidence_sha256` naming a frozen artifact. Probe and review-action arrays contain every scenario finding ID exactly once; actions own the final disposition/scope used by the outcome gate. Rounds are independent execution evidence with a unique nonblank `round_id`, `targeted|full` scope, and a nonempty set of known reviewed finding IDs. The same finding may appear in multiple rounds, including a clean final round with no new findings. `test_count` is the number of added Python `test_*` function definitions, while language-neutral `test_size_lines` is the number of added lines in the frozen test diff. Full/targeted costs count every round record of that scope, not findings; wall time is derived from both runner durations. Self-reported values must match those deterministic results.

Snapshot identities are not runner inputs: finalization generates their 64-hex digests from evaluator-owned evidence. The normalizer accepts only `output-freeze.json`, validates the terminal seal, both phase bundles and lineage, the exact output shape, and every frozen artifact size/digest before reading behavior; revalidates the structured records and derived costs; recursively redacts paths, commit IDs, declared clues, and the identity denylist from all blinded strings and object keys; then checks [`behavior-schema.json`](evaluator/behavior-schema.json). Every official normalized input is rederived from the real registered arm freeze and seal; edited or synthetic normalized JSON is rejected.

```bash
python3 evals/deliver/harness.py normalize <arm-stage>/evaluator/output-freeze.json --comparison-manifest <comparison-manifest.json> --output <normalized.json>
python3 evals/deliver/harness.py blind-packet \
  <retry-baseline.json> <retry-candidate.json> <holdout-baseline.json> <holdout-candidate.json> \
  --comparison-manifest <comparison-manifest.json> --output <blind-packet.json>
```

The four inputs are supplied only in the precommitted arm order. The harness groups both scenarios per workflow and assigns Run A/Run B by canonical content digest, freezes the authoritative packet and private map under evaluator control, and only then records the locked blind transition. Start one fresh blind judge, freeze its structured decision, then reveal identity. A judge may restart only after an explicitly recorded external interruption before its record freezes.

```bash
python3 evals/deliver/harness.py begin-judge --comparison-manifest <comparison-manifest.json> --blind-packet <blind-packet.json>
python3 evals/deliver/harness.py freeze-judge --comparison-manifest <comparison-manifest.json> --blind-packet <blind-packet.json> --decision <judge-decision.json> --output <judge-record.json>
python3 evals/deliver/harness.py reveal-identities --comparison-manifest <comparison-manifest.json> --blind-packet <blind-packet.json> --judge-record <judge-record.json> --output <identity-reveal.json>
python3 evals/deliver/harness.py check-candidate-compliance <candidate-fields.json> --comparison-manifest <comparison-manifest.json> --identity-reveal <identity-reveal.json> --blind-packet <blind-packet.json> --judge-record <judge-record.json> --output <candidate-compliance.json>
```

Every artifact binds the comparison/evaluator identity and SHA-256 of every upstream file it consumed. Candidate fields remain post-reveal only and must contain exact schema types, six unique frozen-ledger IDs, and no missing or extra finding.

## Frozen outcome gate

After both identities are revealed, run the deterministic category and cost gate directly on the four already-validated normalized outputs—one output per scenario for each arm:

```bash
python3 evals/deliver/harness.py gate-official \
  --comparison-manifest <comparison-manifest.json> \
  --baseline <baseline-retry-normalized.json> <baseline-holdout-normalized.json> \
  --candidate <candidate-retry-normalized.json> <candidate-holdout-normalized.json> \
  --blind-packet <blind-packet.json> \
  --judge-record <judge-record.json> \
  --identity-reveal <identity-reveal.json> \
  --candidate-compliance <candidate-compliance.json> \
  --output <outcome-gate.json>
```

The command validates every normalized document, requires both scenarios exactly once per arm, extracts their exact `review_actions`, and fails on missing or extra findings, any candidate category that differs from the frozen ledger, or failure to improve strictly on both cost axes. The axes are unjustified `permanent` decisions where the ledger expects `table_case`, `probe_only`, or `no_test`, and unnecessary `full` rereviews where the ledger expects `targeted` or no rereview. Its machine-readable output includes each input SHA-256, counts, category regressions, the ledger hash, and the pass decision.

The official gate additionally requires candidate compliance, preserved material correctness, and a blinded candidate-better verdict. A frozen judge `inconclusive` result maps to `inconclusive/uncomparable_runs`. A terminal failure instead requires exact structured observations bound to the comparison and attempt-state projection; the harness derives the highest-precedence failure class. `freeze-final-verdict` copies the complete chain to canonical evaluator-owned paths. Merge rereview runs `validate-final-verdict --comparison-manifest <comparison-manifest.json>` to replay that chain and its state hash. `cleanup-comparison` validates the same replay, records a cleanup receipt, and retains the verified external sentinel through merge rereview. Only after that rereview and the terminal merge-or-abandon closeout may the operator delete the exact sentinel path recorded in the comparison manifest; deletion ends further replay validation and is not part of `cleanup-comparison`.

## Evaluator order and evidence

The evaluator freezes, in order: both runner phases; the single arm finalization and terminal seal; acceptance and diagnostic probe results; normalized packets; blinded verdict; identity reveal; candidate compliance; ledger gate; final verdict. Preserve all of them in the `$skill-review` scratch root and summarize them in its durable state document. The outcome gate consumes the normalized outputs themselves, so there is no later transcription artifact or second source of workflow decisions.

The hard ledger gate requires every registered outcome before the qualitative judge can prefer the candidate. The blinded judge uses [`judge-rubric.md`](evaluator/judge-rubric.md): correctness first, then durable test value, consolidation, rereview breadth, test count/size, full rounds, wall time, and ceremony. No hard line-count cap applies.

## Harness checks

```bash
python3 -m unittest discover -s evals/deliver/tests -v
python3 evals/deliver/harness.py validate-ledger
git diff --check
```
