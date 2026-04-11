---
name: first-principles-mode
description: Use when the user requests `engage first-principles mode "..."` and needs a breadth-first, read-only analysis pass that favors conceptual models, system logic, competing hypotheses, and plain-language synthesis before narrow technical judgment or implementation work.
---

# First-Principles Mode Skill

Run a deliberately broad, read-only analysis pass before offering implementation judgment.

Load `skills/first-principles-mode/references/analysis-rubric.md` before starting.

## Trigger

Accept:

- `engage first-principles mode "..."`

Treat the quoted topic as the analysis target. Do not require the user to restate it in a second command.

## Goal

Produce the most thorough useful explanation by understanding the system at the mechanism level first, then narrowing only after the broad model is stable.

## Working Posture

- Read broadly before drilling into file-local detail.
- Prefer conceptual models, system logic, incentives, boundaries, and failure dynamics before implementation judgment.
- Explain in plain language first, then add technical detail.
- Be thorough internally and concise externally.
- Stay read-only by default.
- If the same request also asks for edits, debugging, refactors, or fixes, complete the analytical pass first and stop there. Wait for an explicit follow-up before changing files.
- Use multiple candidate explanations when the answer is ambiguous. Do not anchor on the first plausible story.
- Back conclusions with file-backed evidence or other observable artifacts from the repo.

## Workflow

1. Restate the user's question in simple terms and make the success criterion explicit.
2. Run a breadth pass across the repo or materials before zooming in:
   - top-level docs and manifests
   - entrypoints and router surfaces
   - public interfaces and system seams
   - CI, deployment, and operational wiring when relevant
   - representative flows across major subsystems
3. Decompose the investigation internally into a small set of subquestions.
   - Keep the subquestions internal by default.
   - Use them to cover product thesis, system boundaries, control/data flow, incentives, constraints, bottlenecks, and likely failure modes as relevant to the prompt.
   - Ask the user follow-up questions only when a material ambiguity cannot be resolved from available evidence.
4. Build 2-4 competing hypotheses when more than one explanation is plausible.
5. Gather confirming and disconfirming evidence before choosing the best explanation.
6. Recompose the findings into one coherent answer that starts plain and becomes more technical only as needed.
7. Choose the smallest user-facing output shape that preserves the conclusion, confidence, and decisive evidence.
   - Keep internal subquestions, discarded hypotheses, and intermediate reasoning private unless surfacing them will materially help the user.
   - Prefer a tight causal memo over a report template when the thesis is clear.
   - Expand only when ambiguity, confidence, or decision risk justifies it.
8. Stop after the analysis pass. Do not move into implementation, patching, or task execution.

## Output Contract

Default to a tight causal memo, not a sectioned report.

Use this shape unless the user asks for a deep dive or the ambiguity is genuinely high:

1. Open with the answer in plain language.
2. Develop the diagnosis through 4-7 causal claims or mechanism paragraphs.
3. Attach evidence inline where each claim needs support.
4. End with implications, fix order, or next steps only if the user asked for them or they are necessary to make the diagnosis useful.

Usually this should be:

- one short opening verdict paragraph
- then a short run of dense paragraphs or bullets, each carrying one major causal point
- sometimes a short closing paragraph on implications

Formatting rules:

- Headings are optional. Use them only when they reduce cognitive load.
- Prefer paragraph flow over section stacks.
- Prefer inline evidence over a standalone evidence section.
- Keep competing hypotheses, assumptions, hidden constraints, risks, and unresolved questions internal by default.
- Surface those items only when they materially change the conclusion, confidence, or next decision.
- Do not expose the internal subquestion list unless the user asks for the reasoning structure.
- Do not mirror every internal analysis stage as a user-facing section heading.
- Avoid labels like `Mental model`, `Chosen explanation`, or `File-backed evidence` unless they genuinely improve readability for that answer.

## Anti-Defaults

- Do not jump straight into patching.
- Do not over-index on one file or subsystem before mapping the broader system.
- Do not lead with verification minutiae unless they are central to the causal explanation.
- Do not confuse a symptom list with a mechanism.
- Do not present high confidence when the evidence is mixed or incomplete.
- Do not force a long sectioned template onto every answer.
- Do not turn the visible answer into a transcript of the internal reasoning process.

## Example Prompts

- `engage first-principles mode "Explain why this system keeps collapsing under growth"`
- `engage first-principles mode "Read this repo and tell me what the actual product thesis is"`
- `engage first-principles mode "Diagnose the root cause of this architecture drift; do not propose fixes yet"`
