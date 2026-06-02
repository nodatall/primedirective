# Clarifier Skill

Goal: Add an installable Clarifier skill that coaches revision without turning into ghostwriting.

Fast mode note: Initial plan-review pause skipped by --fast; continue into implementation after refinement unless a fast-mode stop condition applies.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The user wants an explicit `$clarifier` invocation.
- The core stance is question-led, example-capable, and user-rewrite-required.
- Saving drafts or tone-library samples is out of scope for this pass.
- Roughdraft, `rd`, and CriticMarkup must stay opt-in only.

## Steps

### 1. Add the skill

- [x] Create a new `skills/clarifier/SKILL.md` with concise metadata and workflow instructions.
- [x] Keep the skill focused on coaching the user through their own revision loop.
- [x] Include clear rules for short teaching rewrites, emotional safety, stopping, and no default Roughdraft usage.

### 2. Wire the public skill surface

- [x] Add Clarifier to the README quick reference and skill details.
- [x] Check the validator and installer expectations, then update only the real public mirrors they enforce.

### 3. Validate and close out

- [x] Run the required skill-contract and whitespace checks.
- [x] Run the Codex plugin installer so the local installed skill surface is current.
- [x] Do a final review of the branch against this plan and fix any material issues.
- [x] Archive this execution plan and commit the completed work.
