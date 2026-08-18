# Deliver Regression Eval Suite v3

This tracked suite compares two versions of the `$deliver` contract through the existing `$skill-review` workflow. It does not add an orchestration layer. The suite freezes two scenarios, evaluator outcomes, runner isolation, staged review packets, normalization, and the blinded judge contract.

## Required invocation

Run from the Prime Directive repository with fresh `gpt-5.6-sol` runners at `xhigh` reasoning:

```text
$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=<ref> candidate=<ref-or-worktree> --preserve-review-artifacts
```

`$skill-review` owns baseline/candidate reconstruction, fresh runner and judge allocation, the durable state document, and preserved scratch root. This suite supplies the realistic scenarios and deterministic gates. Use the same runner model, reasoning, tools, outer execution boundary, and local-only stop boundary for both arms. Do not use native Plan mode or Pro analysis in this required regression lane.

This v3 iteration retains the v2 active-execution budget for every baseline and candidate arm: 90 minutes total across its pre-packet and remediation phases, with a 15-minute inactivity timeout. Inactivity means no structurally valid event from the fixed Codex JSONL event-type allowlist has arrived on runner stdout; unknown, fabricated, malformed, partial, or arbitrary bytes do not extend the deadline. The earlier 900-second and 1,800-second candidate attempts did not produce authoritative terminal traces. The later v2 Queuectl arms completed, but the historical holdout disclosed its defect-specific acceptance contract before packet staging. All earlier attempts remain diagnostic artifacts and are excluded from v3 scoring.

## Frozen scenarios

1. [`retry-failed`](retry-failed/scenario.json) is the original Queuectl known case. The clean fixture preserves the pilot's semantic contents with only trailing blank EOF lines normalized, then freezes that normalized tree and every fixture-file hash. Its three public tests, source bullets, acceptance contract, fixed approval, and original seven hidden checks remain the pilot cases. Its eleven later reviewer-derived checks are unchanged diagnostic post-hoc challenges, not unbiased acceptance checks.
2. [`preflight-remediation-holdout`](preflight-remediation-holdout/scenario.json) replays the already-approved May 30 remediation from the two required scripts at exact commit `27103d3a05eb20072d29917532326a5cbd59dc8f`. The fixture records the source commit, source tree, and exact blob/mode for each script but deliberately does not materialize the rest of that historical repository, so the runner sees only one Deliver contract: the separately extracted arm package. Before packet staging the runner sees only a generic inspection-only starting-state contract. The packet later supplies the corrupt-throttle and asynchronous-preflight findings, deterministic versions of the original probes, the paused plan, and the behavior later fixed in `2e0c01916bebceca619f1b209a101e591ebfd07d`.

The evaluator-owned [`outcome-ledger.json`](evaluator/outcome-ledger.json) is frozen before contract edits. It is not supplied to either runner. It spans all four test dispositions and both rereview scopes.

## Staged protocol

For each scenario and each arm:

1. Preflight the only compatible runner binary. This command never falls back to `PATH` or Homebrew: it resolves `/Applications/ChatGPT.app/Contents/Resources/codex`, records its absolute path, version, executable SHA-256, and the arm timeout policy, and performs a tiny real Sol/xhigh JSONL smoke under the same outer sandbox used for scenarios. The smoke has its own fixed two-minute total and one-minute inactivity limits so preflight stays quick; both policies are validated from the preserved preflight artifact. Preserve that evaluator artifact in the `$skill-review` scratch root:

   ```bash
   python3 evals/deliver/harness.py preflight-runner --output <runner-preflight.json>
   ```

2. Extract only that arm's Deliver contract and required references through `$skill-review` into one package directory. Preserve their package-relative paths.
3. Prepare an empty stage at `/private/tmp/deliver-eval-<run>/<scenario>-<baseline|candidate>`. A runtime root may contain only the four stable arm names plus the harness sibling probe; run the arms sequentially through the harness. This builds a fresh deterministic git snapshot and a hash-allowlisted input manifest, validates the runner identity again, and copies the preflight artifact into evaluator evidence:

   ```bash
   python3 evals/deliver/harness.py prepare --scenario retry-failed --contract <extracted-contract-package> --destination <arm-stage> --runner-preflight <runner-preflight.json>
   python3 evals/deliver/harness.py verify-manifest <arm-stage>
   ```

4. Start the pre-packet runner through the harness. This invokes the preflight-pinned bundled Codex with actual `exec --json --ephemeral --ignore-user-config --strict-config`, fixed `gpt-5.6-sol`/`xhigh`, and `--dangerously-bypass-approvals-and-sandbox`. That bypass flag is used only because `/usr/bin/sandbox-exec` is the sole execution boundary; nesting Codex's workspace sandbox under Seatbelt is unsupported. `/usr/bin/env -i` and `Popen(env=...)` supply exactly arm-local `CODEX_HOME`, `HOME`, and `TMPDIR`, a fixed minimal `PATH`, and fixed nonsecret locale/terminal values. The generated profile allows normal process, network, and current-arm behavior, denies reads and writes under `/Users/fromdarkness` and `/Volumes`, and denies every other stable or existing sibling directory in that run root. Tool subprocesses inherit it. Authentication is copied atomically at mode 0600 and removed when the harness observes a structurally valid `thread.started`, with unconditional cleanup on success or failure. Every prompt begins with the same exact first-tool gate; an execution is accepted only when no actionable tool precedes it and the gate shell tool proves that the copy is absent, an inherited sentinel is absent, and the sibling probe is unreadable, then exits 0 with the exact gate output. This is a fail-closed trace condition, not a claim about scheduler ordering before the observed event. The harness starts the runner in a new session/process group and streams stdout into a parent-owned path under the Seatbelt-denied sibling probe, flushing every chunk while independently accumulating its byte count and SHA-256. Only structurally valid allowlisted Codex events refresh the 15-minute inactivity deadline. After the entire process group is stopped and the leader reaped, the harness rejects a replaced or changed stream unless its regular-file type, size, and digest still match that parent capture, then atomically publishes the verified bytes as `trace.jsonl`. Stderr uses the same denied parent location and post-group atomic publication. The remediation phase receives only the unused portion of the arm's 90-minute total. Metadata records the fixed timeout policy and prior phase consumption alongside `execution_boundary=outer_sandbox_only`, the exact environment/wrapper command/profile digest, and the binary path/version/digest/preflight binding. The remaining prompt comes only from hashed contract and scenario-stage files. Authoritative JSONL, stderr, metadata, prompt, profile, and input manifest are written under `<arm-stage>/runner/pre-packet/`; `$skill-review` remains the outer arm/judge orchestrator.

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

   This is the only arm-finalization path; it accepts no caller-selected trace. It requires both harness-produced runner phases and verifies their exact outer-sandbox commands, phase identities, successful exits, prompt/trace/stderr/profile digests, initial snapshot, manifest lineage, identical timeout policy, and cumulative arm-budget accounting. Each trace must begin with exactly one `thread.started`, end with exactly one successful `turn.completed`, and contain no failure terminal or trailing event. The pre-packet input digest must equal the review manifest parent and the remediation input digest must equal the current manifest. Diffs are recomputed from the initially prepared fixture commit, not current `HEAD`, and include committed deltas, staged/unstaged worktree deltas, and untracked code or tests. The command freezes both complete runner evidence bundles, the pre-packet snapshot and validation bytes, code, tests, probes, reviews, and the run record under `evaluator/frozen/`; writes [`output-freeze.json`](evaluator/output-freeze-schema.json); and writes a digest-bound [`terminal-seal.json`](evaluator/terminal-seal-schema.json). Normalization independently revalidates that seal, both runner bundles, and the timeout-policy binding.

   If either deadline expires, the harness sends `SIGKILL` to the isolated runner process group, reaps the leader, removes the arm-local authentication copy, integrity-checks and publishes the already-flushed partial trace and stderr as diagnostics, and raises without writing valid runner metadata. Cleanup repeats the safe process-group stop even when the leader exited first so background descendants cannot survive. The harness refuses to signal its own process group. Without valid metadata, finalization and terminal sealing remain impossible; the timed-out arm is excluded rather than scored.

7. Run the original hidden checks and historical probes unchanged. Run post-hoc Queuectl challenges separately and label their results `diagnostic_posthoc`; they cannot alter acceptance-check totals.
8. Normalize each finalized arm and build the blind pair. Judge behavior first. Reveal workflow identity and run candidate-only contract compliance only after the blinded verdict is frozen.

The packet-staging command refuses to run without `evidence/pre-packet-snapshot.json`. Preparation rejects nonempty destinations, symlinks, escaping paths, evaluator/ledger names, multiple or non-Deliver `SKILL.md` files, a drifted historical commit/tree/blob, and any unlisted input. Each manifest and every listed file has a SHA-256 digest.

The threat model separates the trusted evaluator/operator from the untrusted runner. The inherited outer sandbox is the only isolation boundary: it keeps user and volume data plus sibling arms unreadable and unwritable while leaving the current `/private/tmp` arm usable. The empty environment prevents parent token variables from entering the boundary. The first-tool gate, trace checks, frozen digests, and terminal seal are fail-closed lifecycle and audit controls, not a second sandbox. They detect partial or accidental mutation; a trusted operator able to rewrite every local artifact can forge a new digest chain, so the seal is not claimed as protection from that operator.

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

Snapshot identities are not runner inputs: finalization generates their 64-hex digests from evaluator-owned evidence. The normalizer accepts only `output-freeze.json`, validates the terminal seal, both phase bundles and lineage, the exact output shape, and every frozen artifact size/digest before reading behavior; revalidates the structured records and derived costs; recursively redacts paths, commit IDs, declared clues, and the identity denylist from all blinded strings and object keys; then checks [`behavior-schema.json`](evaluator/behavior-schema.json).

```bash
python3 evals/deliver/harness.py normalize <arm-stage>/evaluator/output-freeze.json --output <normalized.json>
python3 evals/deliver/harness.py blind-packet <normalized-1.json> <normalized-2.json> --output <blind-packet.json>
```

Blind labeling is assigned by normalized-content digest, so swapping input arm order produces byte-identical Run A/Run B packets. Candidate field compliance is a separate post-reveal artifact and must never appear in `run-record.json`. After reveal, provide only the candidate's structured field report. It must use exact schema types, six unique nonblank frozen-ledger IDs, and no missing or extra finding before the separate check passes:

```bash
python3 evals/deliver/harness.py check-candidate-compliance <candidate-fields.json> --output <candidate-compliance.json>
```

## Frozen outcome gate

After both identities are revealed, run the deterministic category and cost gate directly on the four already-validated normalized outputs—one output per scenario for each arm:

```bash
python3 evals/deliver/harness.py gate-outcomes \
  --baseline <baseline-retry-normalized.json> <baseline-holdout-normalized.json> \
  --candidate <candidate-retry-normalized.json> <candidate-holdout-normalized.json> \
  --output <outcome-gate.json>
```

The command validates every normalized document, requires both scenarios exactly once per arm, extracts their exact `review_actions`, and fails on missing or extra findings, any candidate category that differs from the frozen ledger, or failure to improve strictly on both cost axes. The axes are unjustified `permanent` decisions where the ledger expects `table_case`, `probe_only`, or `no_test`, and unnecessary `full` rereviews where the ledger expects `targeted` or no rereview. Its machine-readable output includes each input SHA-256, counts, category regressions, the ledger hash, and the pass decision.

This gate evaluates only frozen category retention and the two cost axes. Material correctness and the blinded judge verdict remain separate required gates; `gate-outcomes` reports both as unevaluated and cannot claim the overall candidate verdict.

## Evaluator order and evidence

The evaluator freezes, in order: both runner phases; the single arm finalization and terminal seal; acceptance and diagnostic probe results; normalized packets; blinded verdict; identity reveal; candidate compliance; ledger gate; final verdict. Preserve all of them in the `$skill-review` scratch root and summarize them in its durable state document. The outcome gate consumes the normalized outputs themselves, so there is no later transcription artifact or second source of workflow decisions.

The hard ledger gate requires every registered outcome before the qualitative judge can prefer the candidate. The blinded judge uses [`judge-rubric.md`](evaluator/judge-rubric.md): correctness first, then durable test value, consolidation, rereview breadth, test count/size, full rounds, wall time, and ceremony. No hard line-count cap applies.

## Harness checks

```bash
python3 -m unittest discover -s evals/deliver/tests -v
python3 evals/deliver/harness.py validate-ledger
git diff --check
```
