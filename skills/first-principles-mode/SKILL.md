---
name: first-principles-mode
description: Run a deep, adaptive, read-only analysis pass that widens the search space, tests competing explanations, and synthesizes the best mechanism-level answer before implementation judgment. Supports `--pro` for ChatGPT Pro browser escalation through the repo wrapper.
---

# First-Principles Mode Skill

Run a deliberately deep, adaptive, read-only analysis pass before offering implementation judgment.

Load `skills/first-principles-mode/references/analysis-rubric.md` before starting.

If `--pro` is present, also load `skills/shared/references/analysis/pro-oracle-escalation.md`.

## Activation

Invoke explicitly with `$first-principles-mode`.

Treat the current user request as the analysis target. Do not require the user to restate it in a second command.

Supported modifiers:

- `--pro`

## Goal

Produce the most useful answer for hard, ambiguous, or repeated-failure problems by understanding the system or question at the mechanism level first, then narrowing only after the search space has been widened and the leading explanation has survived scrutiny.

## Working Posture

- Default to deep analysis, not lightweight explanation.
- Start by inferring what kind of problem this is before choosing an analysis frame.
- Read broadly before drilling into file-local detail.
- Prefer conceptual models, system logic, incentives, boundaries, hidden constraints, and failure dynamics before implementation judgment.
- Widen the search space before refining the answer.
- Generate materially different candidate explanations or approaches when more than one path is plausible. Avoid cosmetic variants of the same idea.
- Try to disconfirm the leading explanation before settling on it.
- Separate observation, inference, and synthesis internally, and surface the distinction when it matters.
- Explain in plain language first, then add technical detail.
- Spend available reasoning effort on search, comparison, and falsification rather than on polishing prose.
- Be thorough internally and concise externally.
- Stay read-only by default.
- If the same request also asks for edits, debugging, refactors, or fixes, complete the analytical pass first and stop there. Wait for an explicit follow-up before changing files.
- Back conclusions with file-backed evidence or other observable artifacts from the repo.
- State confidence and the key uncertainty when they materially affect the conclusion.
- With `--pro`, use the Oracle Pro escalation reference after local reconnaissance. Oracle is an implementation detail: choose context, dry-run, run the Pro pass, then synthesize against local evidence.

## Workflow

1. Restate the user's question in simple terms and make the success criterion explicit.
2. Infer the problem shape before locking into an analysis frame.
   - Determine what kind of question this is by observing the materials, not by assuming the first framing is correct.
   - Choose the smallest analysis frame that can still explain the problem faithfully.
3. Run a breadth pass across the repo or materials before zooming in:
   - top-level docs and manifests
   - entrypoints and router surfaces
   - public interfaces and system seams
   - CI, deployment, and operational wiring when relevant
   - representative flows across major subsystems
4. Decompose the investigation internally into a small set of subquestions.
   - Keep the subquestions internal by default.
   - Use them to cover the mechanisms, constraints, boundaries, incentives, failure modes, and unknowns most likely to unlock this case.
   - Ask the user follow-up questions only when a material ambiguity cannot be resolved from available evidence.
5. Build multiple materially different candidate explanations, approaches, or framings when more than one is plausible.
   - Do not settle on the first plausible story.
   - Prefer candidates that would lead to meaningfully different conclusions or decisions.
6. Gather confirming and disconfirming evidence before choosing the best explanation.
   - Use file-backed observations, control-flow traces, contracts, config, or operational artifacts when relevant.
   - Distinguish what the evidence shows from what it merely suggests.
7. If `--pro` is present, run the Pro escalation after the local breadth pass has identified the problem shape and likely context.
   - Use `./scripts/oracle-pro.sh dry-run` first.
   - Use filtered whole-repo context for small or broad questions; use curated files for large or narrow questions.
   - Stop before sending only when the dry-run or local inspection reveals likely secrets, private data, or an obviously wrong context bundle.
   - Treat the Pro result as external analysis to verify and synthesize, not as source of truth.
8. Run an explicit adversarial pass against the current best view.
   - Ask what would falsify it.
   - Look for hidden assumptions, missing constraints, or a broader framing that changes the problem shape.
   - If the evidence remains mixed, keep the answer mixed.
9. Recompose the findings into one coherent answer that starts plain and becomes more technical only as needed.
10. Choose the smallest user-facing output shape that preserves the conclusion, confidence, and decisive evidence.
   - Keep internal subquestions, discarded hypotheses, and intermediate reasoning private unless surfacing them will materially help the user.
   - Prefer a tight causal memo over a report template when the thesis is clear.
   - Expand only when ambiguity, confidence, or decision risk justifies it.
11. Stop after the analysis pass. Do not move into implementation, patching, or task execution.

## Output Contract

Default to a tight causal memo, not a sectioned report.

Use this shape unless the user asks for a deep dive or the ambiguity is genuinely high:

1. Open with the answer in plain language.
2. Develop the diagnosis through 4-7 causal claims or mechanism paragraphs.
3. Attach evidence inline where each claim needs support.
4. When material, include a brief note on confidence, key uncertainty, or the evidence gap most likely to change the answer.
5. End with implications, fix order, or next steps only if the user asked for them or they are necessary to make the diagnosis useful.

Usually this should be:

- one short opening verdict paragraph
- then a short run of dense paragraphs or bullets, each carrying one major causal point
- sometimes a short closing paragraph on uncertainty, implications, or next steps

Formatting rules:

- Headings are optional. Use them only when they reduce cognitive load.
- Prefer paragraph flow over section stacks.
- Prefer inline evidence over a standalone evidence section.
- Keep competing hypotheses, assumptions, hidden constraints, risks, and unresolved questions internal by default.
- Surface those items only when they materially change the conclusion, confidence, or next decision.
- Do not expose the internal subquestion list unless the user asks for the reasoning structure.
- Do not mirror every internal analysis stage as a user-facing section heading.
- Avoid labels like `Mental model`, `Chosen explanation`, or `File-backed evidence` unless they genuinely improve readability for that answer.
- Do not mistake a longer answer for a deeper answer.

## Anti-Defaults

- Do not jump straight into patching.
- Do not over-index on one file or subsystem before mapping the broader system.
- Do not stay trapped inside the user's initial framing if the evidence suggests the problem is misframed.
- Do not lead with verification minutiae unless they are central to the causal explanation.
- Do not confuse a symptom list with a mechanism.
- Do not confuse polish with search.
- Do not present multiple hypotheses that are only superficial variations of the same story.
- Do not present high confidence when the evidence is mixed or incomplete.
- Do not manufacture complexity when the simplest explanation is well-supported.
- Do not force a long sectioned template onto every answer.
- Do not turn the visible answer into a transcript of the internal reasoning process.

## Example Prompts

- `$first-principles-mode Explain why this system keeps collapsing under growth`
- `$first-principles-mode Read this repo and tell me what the actual product thesis is`
- `$first-principles-mode Diagnose the root cause of this architecture drift; do not propose fixes yet`
- `$first-principles-mode Pressure-test this plan and tell me where its reasoning breaks`
- `$first-principles-mode Find a materially different way to solve this problem, not just an optimization of the current path`
- `$first-principles-mode --pro Explain the real architecture risk in this repo`
