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

Setup intentionally skips thinking-time UI selection and model-picker selection because it is only a login/profile check. Normal dry-run, run, and render actions use extended thinking by default because the ChatGPT Pro picker may expose only Standard and Extended. Use `ORACLE_PRO_THINKING=heavy` only when that option exists, or rerun with `ORACLE_PRO_THINKING=off` if the thinking-time control is unavailable.

If ChatGPT is logged in but Oracle reports that it cannot locate the model selector, this is usually ChatGPT UI drift or a hidden picker, not proof that the profile is signed out. For a real run where the prompt box is visible but the picker is hidden, use:

```bash
ORACLE_PRO_MODEL_STRATEGY=ignore ORACLE_PRO_THINKING=off ./scripts/oracle-pro.sh run -p "<prompt>" --file .
```

This skips forced model and thinking-time selection. Record the result as using the current ChatGPT browser mode rather than a verified model-picker selection.

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

## Plan-And-Execute Gates

These gates apply when the caller is `$plan-and-execute --pro-analysis`.

### Pre-Oracle gate

Before running `oracle-pro.sh dry-run`, `oracle-pro.sh run`, or `oracle-pro.sh render`, confirm the plan key and the current planning phase.

When `--deep-research` is also active, the gate is hard:

- `tasks/prd-<plan-key>.md` and `tasks/tdd-<plan-key>.md` exist as initial drafts.
- `tasks/tmp/research-plan-<plan-key>.md` exists.
- The research memo contains a Deep Research Completion Stamp with `evidence_bar_met: yes`.
- The PRD/TDD have been revised from adopted research findings, or the research memo records that no PRD/TDD section changes were needed.
- No current research finding marked adopted is still waiting to be reflected in PRD/TDD or explicitly deferred/rejected with a reason.

If any pre-Oracle check fails, stop. Do not run Oracle dry-run as a substitute for the missing research pass. Report the unmet gate and complete or repair deep research first.

### Post-Oracle synthesis gate

After `oracle-pro.sh run` returns, read the Pro answer and synthesize it before generating tasks or starting refinement.

For `$plan-and-execute --pro-analysis`, write `tasks/tmp/pro-analysis-<plan-key>.md` with:

- context bundle summary: files or scope sent to Pro, token estimate if known, and any excluded risky/noisy paths
- Pro findings ledger: stable finding ID, Pro claim, local verification evidence, disposition (`adopted`, `rejected`, `deferred`), and disposition reason
- conflict reconciliation: conflicts with repo evidence, the deep-research memo, PRD, or TDD, and how each conflict was resolved
- artifact delta: PRD/TDD sections changed, task-plan inputs created, and source-backed claims independently verified when Pro suggested external sources
- Pro synthesis completion stamp containing `oracle_result_read`, `findings_reconciled`, `artifact_changes_applied`, `unresolved_blockers`, and `pro_synthesis_complete`

Before setting `pro_synthesis_complete: yes`, print a short `Pro Findings Summary` in the visible thread/log: adopted, rejected/deferred, blockers, and artifact changes.

Set `pro_synthesis_complete: yes` only when the Pro answer was read, every material Pro finding has a disposition, adopted findings have been applied to PRD/TDD or converted into explicit task-plan inputs, conflicts have been reconciled, the visible findings summary was emitted, and no unresolved blocker remains.

If `pro_synthesis_complete` is missing or not `yes`, stop. Do not generate `tasks-plan`, run `$plan-refine`, or execute.

Use this order:

1. Read the request and infer the analysis target.
2. Inspect repo shape with fast local commands such as `pwd`, `git status --short`, `rg --files`, top-level docs, manifests, CI config, and the files most likely to own the behavior.
3. For `$plan-and-execute --pro-analysis`, satisfy the pre-Oracle gate above before any dry-run with selected plan context.
4. Decide whether the run needs whole-repo or curated context.
5. Run a dry-run token/file report before the real Pro call.
6. Send the chosen bundle only after the dry-run looks reasonable.
7. Read the Pro result and synthesize it against local evidence before answering or changing artifacts.
8. For `$plan-and-execute --pro-analysis`, satisfy the post-Oracle synthesis gate before tasks-plan generation, refinement, or execution.

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

For `$plan-and-execute --pro-analysis`, raw Oracle output is not a sufficient synthesis artifact. The Pro answer must be reduced into `tasks/tmp/pro-analysis-<plan-key>.md`, a short `Pro Findings Summary` must be printed in the visible thread/log, and the memo must end with `pro_synthesis_complete: yes` before downstream planning continues.

For `$repo-sweep --pro-analysis`, use the synthesized findings as Round 1 audit-thesis input before the no-edit audit and review-chain report. If `--loop` is also present, do not rerun Pro every loop round by default; use fresh local review subagents for resweeps unless the user explicitly asks for another Pro pass.
