# Analysis Rubric

Use this rubric to make the analysis deeper, broader, and more faithful than a normal high-effort answer.

## Core Standard

Optimize for explanation quality, not just answer length.

The answer should:

- widen the search space before converging
- explain how the system works
- identify why the observed behavior emerges
- compare materially different plausible explanations or approaches before settling
- separate evidence from inference and synthesis
- try to falsify the leading view before finalizing it
- report material uncertainty honestly
- stop before execution

Run the full analysis internally, but do not assume the user wants to see every analysis stage.

## Internal Vs Visible Work

Treat the rubric as an internal working process, not a mandatory output template.

- Do the full breadth pass, decomposition, and hypothesis comparison internally.
- Show only the parts that help the user understand the answer or make the next decision.
- Default to the shortest shape that preserves the thesis, mechanism, and decisive evidence.
- Expand only when ambiguity, confidence, or stakes justify the extra detail.
- Do not emit a long heading stack just because the internal process had many steps.
- Prefer a memo or argument shape over a report shape.
- Do not mistake a polished visible answer for a sufficiently deep internal search.

## Breadth Pass

Start wide before going deep.

Survey the smallest set of materials that reveals the shape of the whole system:

- top-level README, docs, and package or build manifests
- main entrypoints, routers, jobs, workers, and other control surfaces
- domain boundaries, public interfaces, and cross-cutting infrastructure
- representative happy-path flows
- CI, deploy, or operational wiring if the question touches growth, failures, or reliability

Do not spend most of the time inside one file until the broader map is clear.

Infer the problem shape before committing to a reasoning frame.

- Determine whether the task is mainly diagnostic, explanatory, comparative, design-oriented, or something else.
- Let the evidence refine the framing if the initial user framing appears incomplete or misleading.
- Use the smallest analysis frame that still captures the real mechanism.

## Internal Decomposition

Break the investigation into a few internal subquestions. These are for the analysis process, not user-facing questions by default.

Possible subquestion angles:

- What is the system or product actually trying to optimize for?
- What are the major boundaries and handoff points?
- Where do control flow and data flow diverge?
- Which constraints are explicit, and which are only implicit in code or operations?
- Which failure modes are structural, and which are incidental?
- What gets worse as scale, scope, or coordination increases?

Only ask the user a follow-up question when the ambiguity is material and cannot be resolved from the available materials.

## Hypothesis Discipline

Do not settle on the first plausible explanation.

When more than one answer is plausible:

- generate 2-4 candidate explanations
- collect evidence that supports or weakens each one
- prefer the explanation with the best cross-file support
- say when the evidence is mixed

If one explanation wins because it fits the code but not the docs, say so.

Candidate explanations should be materially different.

- Do not count cosmetic reformulations of the same story as distinct hypotheses.
- Prefer alternatives that would change the conclusion, decision, or recommended next step.
- If the correct answer is likely simple and singular, say so instead of manufacturing extra branches.

## Evidence Standard

Keep evidence concrete and separate from conclusions.

Prefer:

- file-backed observations
- control-flow traces
- config, schema, or contract evidence
- operational or CI wiring when relevant

Mark the difference between:

- observation: what the repo or artifact shows
- inference: what that likely means
- synthesis: the best combined explanation

Run at least one explicit disconfirmation pass.

- Ask what evidence would weaken the current best view.
- Look for hidden constraints, incentives, or boundary conditions that the leading explanation may be skipping.
- If the prompt is about finding alternatives, look for options that change the shape of the problem rather than merely tuning the current approach.

Use reasoning effort for search and comparison first, not for elaborating one early theory.

## Plain-Language First

Use `skills/shared/references/plain-language.md` as the detailed output standard.

Lead with a short explanation a non-specialist could follow.

Then add:

- the mechanism
- the technical details that matter
- the strongest evidence

Do not start with jargon if a simpler explanation can carry the same meaning.

Default user-facing shape:

- one short verdict paragraph
- 4-7 high-signal causal paragraphs or bullets
- evidence attached inline where each claim needs it
- a brief confidence or uncertainty note when it materially affects the answer
- an optional short closing on implications or fix order when the user wants that outcome

Only add explicit sections for assumptions, competing hypotheses, hidden constraints, risks, or unresolved questions when they materially affect the conclusion.

The ideal reading experience should feel like a strong memo from a thoughtful engineer, not a filled-in diagnostic template.

## Anti-Patterns

Watch for these failure modes:

- broad-sounding language without a real breadth pass
- polished prose that never tested alternatives
- multiple hypotheses that are really the same idea wearing different words
- excessive detail that does not change the conclusion
- overstated confidence from partial evidence
- staying trapped inside the initial framing when the deeper issue is elsewhere
- answering with symptoms, preferences, or implementation details instead of mechanism

## Stop Gate

This skill is analysis-first and read-only.

If the user also asks for edits, fixes, refactors, or implementation in the same request:

1. complete the analysis pass
2. state that the diagnosis is complete
3. stop and wait for an explicit follow-up before editing files
