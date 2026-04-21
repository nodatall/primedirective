# Pro Oracle Escalation

Use this reference only when a Prime Directive skill explicitly activates Pro escalation, such as `$first-principles-mode --pro-analysis`, `$plan-and-execute --pro-analysis`, or `$repo-sweep --pro-analysis`.

## Wrapper

Use the repo wrapper, not raw Oracle commands:

```bash
./scripts/oracle-pro.sh setup
./scripts/oracle-pro.sh session
./scripts/oracle-pro.sh dry-run -p "<prompt>" --file .
./scripts/oracle-pro.sh run -p "<prompt>" --file .
```

Resolve the script from the Prime Directive checkout, not from the target project being analyzed. When the current working directory is another repo, invoke the wrapper by its Prime Directive source path while keeping `cwd` in the target repo so `--file .` attaches the target project.

The wrapper owns browser mode, model, thinking-time selection, manual-login profile reuse, upload bundling, timeouts, local temp cleanup, and Oracle invocation details. If no `--file` input is provided, it defaults to `--file .`.

First-time setup is:

```bash
./scripts/oracle-pro.sh setup
```

This opens or reuses the persistent Oracle browser profile. The user may need to sign in to ChatGPT in that browser once. After setup, normal Pro runs should reuse the same profile.

Setup intentionally skips thinking-time UI selection because it is only a login/profile check. Normal dry-run, run, and render actions use extended thinking by default because the ChatGPT Pro picker may expose only Standard and Extended. Use `ORACLE_PRO_THINKING=heavy` only when that option exists, or rerun with `ORACLE_PRO_THINKING=off` if the thinking-time control is unavailable.

For setup, dry-run, run, and render actions, the wrapper gives Oracle a private `TMPDIR` and deletes it after Oracle exits. This removes local `attachments-bundle.txt` files created for browser uploads. Set `ORACLE_PRO_KEEP_TMP=1` only when debugging the generated bundle locally.

If setup reports a duplicate running setup session, reattach through the wrapper:

```bash
./scripts/oracle-pro.sh session
```

If the existing setup session is stale and a fresh one is needed, run:

```bash
./scripts/oracle-pro.sh setup --force
```

## Consent Boundary

An explicit Pro modifier is consent to send selected repo context through the Oracle browser workflow to ChatGPT Pro. Do not ask for a separate approval before every normal Pro run.

Still stop before sending when the dry-run or local inspection indicates likely secret exposure, credentials, private keys, customer data, unrelated personal files, or a context bundle that is obviously too broad for the request. In that case, report the risky paths or category and ask for direction.

## Context Selection

Run local reconnaissance first. Pro escalation does not replace Codex repo inspection.

Use this order:

1. Read the request and infer the analysis target.
2. Inspect repo shape with fast local commands such as `pwd`, `git status --short`, `rg --files`, top-level docs, manifests, CI config, and the files most likely to own the behavior.
3. Decide whether the run needs whole-repo or curated context.
4. Run a dry-run token/file report before the real Pro call.
5. Send the chosen bundle only after the dry-run looks reasonable.
6. Read the Pro result and synthesize it against local evidence before answering or changing artifacts.

Prefer filtered whole-repo context when the repo is small or the question is broad, architectural, product-level, or cross-cutting:

```bash
./scripts/oracle-pro.sh dry-run -p "<standalone prompt>" --file .
./scripts/oracle-pro.sh run -p "<standalone prompt>" --file .
```

Prefer curated context when the dry-run is too large, the task is narrow, or one subsystem clearly dominates:

```bash
./scripts/oracle-pro.sh dry-run -p "<standalone prompt>" \
  --file README.md \
  --file "src/relevant-area/**" \
  --file "tests/relevant-area/**"
```

Include enough context for a fresh model to reason without the local workspace:

- concise project briefing and current goal
- relevant repo map and validation commands
- entrypoints, config, public interfaces, representative tests, and the failing or controversial flow
- constraints, non-goals, and what output is needed

Do not include generated/vendor/build output, secrets, `.env` files, private keys, binary assets unless specifically relevant, or unrelated large fixtures. Oracle already filters common generated directories and honors `.gitignore`, but the agent is still responsible for spotting sensitive or noisy context.

## Dry-Run Interpretation

Use the dry-run report to choose the smallest context that can still answer the question. Whole-repo is acceptable when it is under a practical token budget and file list is clean. If the report is noisy or very large, narrow the file set and rerun dry-run.

Record the final context choice in the visible answer only when it matters for confidence, cost, or reproducibility. Do not make Oracle mechanics the focus of the response.

## Synthesis

Treat the Pro answer as an external reviewer, not as source of truth.

- Check claims against local files, commands, tests, or docs when practical.
- Adopt the ideas that survive local evidence.
- Discard or qualify claims that conflict with the repo.
- Surface uncertainty when local verification is incomplete.

For `$first-principles-mode --pro-analysis`, stop after synthesis unless the user separately asked for edits.

For `$plan-and-execute --pro-analysis`, apply the synthesized findings into planning artifacts and continue execution unless the Pro pass reveals a true blocker that is unsafe, contradictory, or impossible to default.

For `$repo-sweep --pro-analysis`, use the synthesized findings as Round 1 audit-thesis input before the no-edit audit and review-chain report. If `--loop` is also present, do not rerun Pro every loop round by default; use fresh local review subagents for resweeps unless the user explicitly asks for another Pro pass.
