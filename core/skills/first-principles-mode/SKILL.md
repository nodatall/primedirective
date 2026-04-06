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
7. Stop after the analysis pass. Do not move into implementation, patching, or task execution.

## Output Contract

Present results in this order unless the user asks for a different shape:

1. Plain-language thesis
2. Mental model
3. Competing hypotheses considered
4. Chosen explanation and why it won
5. Key assumptions
6. Hidden constraints
7. Core system logic or failure dynamics
8. Risks or breakpoints
9. File-backed evidence
10. Unresolved questions

## Anti-Defaults

- Do not jump straight into patching.
- Do not over-index on one file or subsystem before mapping the broader system.
- Do not lead with verification minutiae unless they are central to the causal explanation.
- Do not confuse a symptom list with a mechanism.
- Do not present high confidence when the evidence is mixed or incomplete.

## Example Prompts

- `engage first-principles mode "Explain why this system keeps collapsing under growth"`
- `engage first-principles mode "Read this repo and tell me what the actual product thesis is"`
- `engage first-principles mode "Diagnose the root cause of this architecture drift; do not propose fixes yet"`
