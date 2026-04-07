# Analysis Rubric

Use this rubric to make the analysis broader, more faithful, and more mechanism-driven than a normal high-effort answer.

## Core Standard

Optimize for explanation quality, not just answer length.

The answer should:

- explain how the system works
- identify why the observed behavior emerges
- compare plausible explanations before settling
- separate evidence from inference
- stop before execution

Run the full analysis internally, but do not assume the user wants to see every analysis stage.

## Internal Vs Visible Work

Treat the rubric as an internal working process, not a mandatory output template.

- Do the full breadth pass, decomposition, and hypothesis comparison internally.
- Show only the parts that help the user understand the answer or make the next decision.
- Default to the shortest shape that preserves the thesis, mechanism, and decisive evidence.
- Expand only when ambiguity, confidence, or stakes justify the extra detail.
- Do not emit a long heading stack just because the internal process had many steps.

## Breadth Pass

Start wide before going deep.

Survey the smallest set of materials that reveals the shape of the whole system:

- top-level README, docs, and package or build manifests
- main entrypoints, routers, jobs, workers, and other control surfaces
- domain boundaries, public interfaces, and cross-cutting infrastructure
- representative happy-path flows
- CI, deploy, or operational wiring if the question touches growth, failures, or reliability

Do not spend most of the time inside one file until the broader map is clear.

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

When the prompt is diagnostic or interpretive:

- generate 2-4 candidate explanations
- collect evidence that supports or weakens each one
- prefer the explanation with the best cross-file support
- say when the evidence is mixed

If one explanation wins because it fits the code but not the docs, say so.

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

## Plain-Language First

Lead with a short explanation a non-specialist could follow.

Then add:

- the mechanism
- the technical details that matter
- the strongest evidence

Do not start with jargon if a simpler explanation can carry the same meaning.

Default user-facing shape:

- one short thesis paragraph
- 3-5 high-signal bullets or short paragraphs explaining the mechanism
- compact inline citations or a short evidence close

Only add explicit sections for assumptions, competing hypotheses, hidden constraints, risks, or unresolved questions when they materially affect the conclusion.

## Stop Gate

This skill is analysis-first and read-only.

If the user also asks for edits, fixes, refactors, or implementation in the same request:

1. complete the analysis pass
2. state that the diagnosis is complete
3. stop and wait for an explicit follow-up before editing files
