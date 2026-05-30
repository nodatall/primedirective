# Pro Browser Analysis

Use this reference only when a Prime Directive skill explicitly activates Pro escalation, such as `$first-principles-mode --pro-analysis`, `$deliver --pro-analysis`, or `$repo-sweep --pro-analysis`.

## Browser Driver

Do not use a third-party browser runner or private automation profile for Pro analysis. The Pro path is a visible ChatGPT browser workflow controlled directly by the agent:

1. Prepare a standalone prompt and a curated context bundle from local files.
2. Use the user's already-authenticated ChatGPT browser session through Chrome automation when available.
3. Fall back to Computer Use only when Chrome automation cannot reliably operate the visible UI.
4. Select the Pro Extended model in the visible ChatGPT UI.
5. Paste or upload the context bundle, submit the prompt, wait for completion, and copy or scrape the answer.
6. Save and synthesize the answer before any downstream planning, refinement, or execution continues.

Chrome automation is the default because it can use the user's real browser session and inspect the DOM. Computer Use is the fallback for UI drift, model-picker changes, attachment controls, or copy buttons that are easier to operate visually than through selectors. If neither driver can operate ChatGPT, stop and report the failed Pro browser gate.

Do not introduce a private browser profile or package-managed browser runner. A Pro browser run must be observable in the user's normal logged-in ChatGPT surface, with visible failure points such as model picker unavailable, composer unavailable, upload failed, no response completed, or answer copy failed.

For any workflow invoked with `--pro-analysis`, a degraded fallback is not a completed Pro pass. If the run did not visibly use Pro Extended, if the answer was not read, or if the browser driver evidence cannot be recorded, the Pro synthesis may be saved for diagnostic value, but it must not set `pro_synthesis_complete: yes`.

## Model Selection Gate

The Pro browser gate requires a visible ChatGPT model label of `Pro Extended` or `Extended Pro` before submission. Treat `Thinking Extended`, `Extended Thinking`, ordinary thinking modes, or any non-Pro label as a failed Pro model-selection gate, even if the prompt was pasted successfully.

Before submitting, explicitly inspect the model picker or composer header, switch to `Pro Extended` or `Extended Pro` when it is not already selected, and re-check the visible label after the switch. If the driver cannot find or select a Pro Extended option, stop and report the failed model-selection gate instead of submitting with the current model.

Record the exact visible model label and how it was verified in the synthesis memo. Set `pro_model_selected: yes` only when the visible selected label was `Pro Extended` or `Extended Pro`.

## Consent Boundary

An explicit Pro modifier is consent to send selected repo context through the visible ChatGPT browser workflow. Do not ask for a separate approval before every normal Pro run.

Still stop before sending when local inspection indicates likely secret exposure, credentials, private keys, customer data, unrelated personal files, or a context bundle that is obviously too broad for the request. In that case, report the risky paths or category and ask for direction.

## Context Selection

Run local reconnaissance first. Pro escalation does not replace Codex repo inspection.

Prefer curated context for narrow implementation plans and filtered whole-repo context only when the repo is small or the question is broad, architectural, product-level, or cross-cutting.

Include enough context for a fresh model to reason without the local workspace:

- concise project briefing and current goal
- relevant repo map and validation commands
- entrypoints, config, public interfaces, representative tests, and the failing or controversial flow
- constraints, non-goals, and what output is needed

Do not include generated/vendor/build output, secrets, `.env` files, private keys, binary assets unless specifically relevant, or unrelated large fixtures.

## Deliver Gates

These gates apply when the caller is `$deliver --pro-analysis`.

### Pre-Browser Gate

Before starting the ChatGPT browser run, confirm the plan key and the current planning phase.

For `$deliver --pro-analysis`, the readable execution plan must already exist as `tasks/execution-plan-<plan-key>.md`. Use that plan plus selected repo context as the Pro browser input. Do not run Pro against only the raw conversation when a deliver plan has not yet been created, and do not require a separate user review before the Pro pass.

When `--deep-research` is also active, the gate is hard:

- `tasks/prd-<plan-key>.md` and `tasks/tdd-<plan-key>.md` exist as initial drafts.
- `tasks/tmp/research-plan-<plan-key>.md` exists.
- The research memo contains a Deep Research Completion Stamp with `evidence_bar_met: yes`.
- The PRD/TDD have been revised from adopted research findings, or the research memo records that no PRD/TDD section changes were needed.
- No current research finding marked adopted is still waiting to be reflected in PRD/TDD or explicitly deferred/rejected with a reason.

If any pre-browser check fails, stop. Do not run the Pro browser pass as a substitute for the missing research pass. Report the unmet gate and complete or repair deep research first.

### Post-Browser Synthesis Gate

After the browser run completes, read the Pro answer and synthesize it before starting refinement.

For `$deliver --pro-analysis`, write `tasks/tmp/pro-analysis-<plan-key>.md` with:

- context bundle summary: files or scope sent to Pro, rough size if known, and any excluded risky/noisy paths
- browser run evidence: driver used (`chrome` or `computer-use`), ChatGPT surface used, exact selected model label, model-selection verification method, submission method (`paste`, `upload`, or both), response completion evidence, and capture method
- Pro findings ledger: stable finding ID, Pro claim, local verification evidence, disposition (`adopted`, `rejected`, `deferred`), and disposition reason
- conflict reconciliation: conflicts with repo evidence, the deep-research memo, or the execution plan, and how each conflict was resolved
- artifact delta: execution-plan sections changed; source-backed claims independently verified when Pro suggested external sources
- Pro synthesis completion stamp containing `pro_result_read`, `pro_browser_run`, `pro_model_selected`, `findings_reconciled`, `artifact_changes_applied`, `unresolved_blockers`, and `pro_synthesis_complete`

Before setting `pro_synthesis_complete: yes`, print a short `Pro Findings Summary` in the visible thread/log: adopted, rejected/deferred, blockers, and artifact changes.

Set `pro_synthesis_complete: yes` only when the Pro answer was read, the browser evidence shows a real ChatGPT browser run with `Pro Extended` or `Extended Pro` visibly selected before submission, every material Pro finding has a disposition, adopted findings have been applied to the `$deliver` execution plan, conflicts have been reconciled, the visible findings summary was emitted, and no unresolved blocker remains.

If `pro_result_read`, `pro_browser_run`, `pro_model_selected`, or `pro_synthesis_complete` is missing or not `yes`, stop. Do not refine a `$deliver` plan or execute.

Use this order:

1. Read the request and infer the analysis target.
2. Inspect repo shape with fast local commands such as `pwd`, `git status --short`, `rg --files`, top-level docs, manifests, CI config, and the files most likely to own the behavior.
3. For `$deliver --pro-analysis`, satisfy the pre-browser gate above before any Pro browser run with selected plan context.
4. Decide whether the run needs whole-repo or curated context.
5. Prepare the smallest context bundle that can still answer the question.
6. Send the chosen bundle through the visible ChatGPT browser only after it looks reasonable and safe.
7. Read the Pro result and synthesize it against local evidence before answering or changing artifacts.
8. For `$deliver --pro-analysis`, satisfy the post-browser synthesis gate before refinement or execution.

## Synthesis

Treat the Pro answer as an external reviewer, not as source of truth.

- Check claims against local files, commands, tests, or docs when practical.
- Adopt the ideas that survive local evidence.
- Discard or qualify claims that conflict with the repo.
- Surface uncertainty when local verification is incomplete.

For `$first-principles-mode --pro-analysis`, stop after synthesis unless the user separately asked for edits.

For `$deliver --pro-analysis`, apply the synthesized findings into the readable execution plan before refinement and either user review or `--fast` implementation unless the Pro pass reveals a true blocker that is unsafe, contradictory, or impossible to default.

For `$deliver --pro-analysis`, raw Pro browser output is not a sufficient synthesis artifact. The Pro answer must be reduced into `tasks/tmp/pro-analysis-<plan-key>.md`, a short `Pro Findings Summary` must be printed in the visible thread/log, and the memo must end with `pro_result_read: yes`, `pro_browser_run: yes`, `pro_model_selected: yes`, and `pro_synthesis_complete: yes` before downstream planning continues.

For `$repo-sweep --pro-analysis`, use the synthesized findings as Round 1 audit-thesis input before the no-edit audit and review-chain report. If running inside `/goal $repo-sweep`, do not rerun Pro every resweep round by default; use fresh local review subagents for resweeps unless the user explicitly asks for another Pro pass.
