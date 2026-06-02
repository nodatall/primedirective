# Clarifier Loop Tuning

Goal: Improve Clarifier so it handles live revision loops more intelligently after the tweet test.

Fast mode note: Initial plan-review pause skipped by --fast; continue into implementation after refinement unless a fast-mode stop condition applies.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The live Clarifier session showed that the skill should remember user constraints during a loop.
- Clarifier should ask for audience or format when it would change the advice, such as tweet versus essay.
- Near the end of a draft, Clarifier should switch from full critique to phrase-level tuning.
- Saving drafts or tone-library samples remains out of scope.
- Roughdraft, `rd`, and CriticMarkup remain opt-in only.

## Steps

### 1. Update the Clarifier contract

- [x] Add an intake rule for audience, format, or destination when those details would change the revision advice.
- [x] Add a session-state rule for current target, user constraints, rejected wording, and preferred wording.
- [x] Add a near-done mode for phrase-level tuning once the draft is already clear.
- [x] Add light format-aware guidance for tweets, essays, and messages without turning Clarifier into a generic editor.

### 2. Keep public surfaces consistent

- [x] Check whether README wording needs a small update after the skill change.
- [x] Preserve the existing no-saving and no-default-Roughdraft boundaries.

### 3. Validate and close out

- [x] Run the required skill-contract and whitespace checks.
- [x] Run the Codex plugin installer so the local installed skill surface is current.
- [x] Do a final review of the branch against this plan and fix any material issues.
- [x] Archive this execution plan and commit the completed work.
