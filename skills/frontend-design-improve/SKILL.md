---
name: frontend-design-improve
description: Use when work changes rendered UI, layout, styling, interaction flows, or visual design and the task needs stronger design direction, originality, and browser-verified polish instead of merely functional frontend output.
---

# Frontend Design Improve Skill

Use this skill for frontend-facing planning, execution, and review work.

Load `skills/frontend-design-improve/references/design-rubric.md` before making user-facing design decisions or grading frontend quality.

## Goal

Raise frontend quality by making design intent explicit, then verifying it in the browser with a skeptical evaluator pass.

This skill is most useful when a task:

- adds or changes rendered UI
- materially affects layout, styling, interactions, or responsive behavior
- needs stronger visual identity or originality
- risks shipping generic AI-looking interface work

Do not use this skill to force a redesign when the task is backend-only or when the repo already has a strict design system that should simply be followed.

## Workflow

1. Decide whether this is:
   - extension of an existing design system
   - a local redesign of one surface
   - a net-new surface that needs a clear visual direction
2. Before coding, write a short design contract in `tasks/tmp/plan-task-<task-id>.md` when task artifacts exist. Keep it concise and include:
   - screens and states being changed
   - the primary user action or flow
   - the intended visual direction
   - anti-goals to avoid generic output
   - acceptance checks for the primary interaction and changed states
   - what browser evidence will be captured in review
3. Build the smallest reviewable slice first:
   - foundation before flourish
   - layout and hierarchy before decorative detail
   - interaction clarity before motion polish
4. After implementation, inspect the real UI in a browser instead of relying on code inspection.
5. Run a skeptical design pass using the rubric:
   - refine the current direction if the design is working
   - pivot if the result is coherent but bland, or if originality is flat
6. Preserve the existing product language when the repo already has an established system. Improve quality within that language instead of inventing a parallel brand.

## Working rules

- Make deliberate choices in typography, spacing rhythm, color, and information hierarchy.
- Prefer one strong visual idea over several weak ones.
- Avoid default component-library composition without meaningful customization.
- Avoid common AI patterns called out in the rubric unless the existing product already uses them intentionally.
- For frontend tasks, treat functional correctness as necessary but not sufficient.
- If a surface is explicitly utilitarian, bias toward clarity and polish rather than forced novelty.

## Review expectation

Frontend review should fail when the work is functional but obviously generic, incoherent, or inconsistent with the stated design contract.
