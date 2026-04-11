# Frontend Design Rubric

Use this rubric when planning, implementing, or reviewing frontend-facing work.

## Core criteria

Score each criterion from 1 to 5.

### 1. Design quality

Judge whether the interface feels like one coherent product rather than a pile of components.

Look for:

- a clear visual direction
- consistent spacing and hierarchy
- typography and color choices that reinforce the same mood
- layout decisions that feel deliberate rather than accidental

Low scores mean the page feels assembled from defaults, visually noisy, or internally inconsistent.

### 2. Originality

Judge whether the work reflects real design decisions instead of template output.

Look for:

- custom composition, pacing, and emphasis
- thoughtful deviations from stock component defaults
- interface details that reflect the product or task context

Penalize:

- obvious template layouts
- unmodified design-system demos
- generic gradient-card hero sections
- interchangeable landing-page patterns that could belong to anything

### 3. Craft

Judge the execution quality of the chosen direction.

Look for:

- solid spacing rhythm
- legible type hierarchy
- sensible contrast
- responsive behavior that preserves hierarchy
- aligned edges, spacing, and control sizing

Low scores mean broken fundamentals, even if the concept is strong.

### 4. Functionality

Judge whether the interface helps the user complete the intended task.

Look for:

- obvious primary actions
- understandable information grouping
- interaction states that make sense
- error and loading states where needed
- keyboard or accessibility basics that are visible in the UI

Low scores mean the user has to guess what to do or cannot complete the flow reliably.

## Hard-fail guidance

- Fail the review if `functionality < 4`.
- Fail the review if `craft < 3`.
- Fail the review if `design quality < 3` or `originality < 3` for work whose value materially depends on user-facing quality.
- When extending an existing utilitarian system, allow originality to be modest, but still fail incoherent or obviously generic output.

## Iteration guidance

- Refine when the direction is promising and the main issues are craft or state coverage.
- Pivot when the work is polished but bland, or when the chosen direction fights the product context.
- Stop adding complexity when it no longer improves the scores.

## Common anti-patterns

- generic purple-gradient-on-white-card aesthetics with no product-specific reason
- oversized hero sections that hide the core task
- decorative motion with weak information hierarchy
- dense controls with no visual grouping
- local visual fixes that make the whole screen less coherent
- frontend work that passes tests but still looks unfinished in the browser
