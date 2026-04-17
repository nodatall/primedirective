# Review Calibration Examples

Use these examples to calibrate review judgment. They are not extra user-facing process; they help the review agent avoid approving work that looks finished but fails the real contract.

## Display-only core feature

Bad approval:

- "The timeline renders tracks and clips, so the editor feature is complete."

Correct finding:

- The contract requires users to move clips on the timeline. Rendering clips is not enough. Review must exercise drag/move behavior and confirm persisted state, undo/redo state, or runtime playback behavior as applicable.

## Stubbed or mocked-away integration

Bad approval:

- "The test passes because the payment provider/client/agent call is mocked."

Correct finding:

- The slice is only complete if the real integration boundary is exercised at the strongest practical level for the repo. A mock-only test can be useful, but review must also verify request shape, error handling, configuration, persistence, webhook/tool callback behavior, or an explicit recorded reason why real integration evidence is not practical.

## UI renders but workflow is broken

Bad approval:

- "The screen loads, the form fields render, and the submit button is visible."

Correct finding:

- The primary user workflow must be completed end-to-end. Review should fill the form, submit it, confirm success or validation behavior, and check resulting UI/API/storage state. A visible button is not evidence that the workflow works.

## Generic frontend passes basic functionality

Bad approval:

- "The page works and uses the component library, so the frontend task is complete."

Correct finding:

- Functional correctness is necessary but not sufficient for frontend-facing work with a design contract. Review should compare against the stated visual direction, anti-goals, changed states, responsive behavior, and browser evidence. Generic default composition can fail even when it is technically usable.

## API route exists but realistic behavior fails

Bad approval:

- "The route exists and returns a 200 in the happy-path unit test."

Correct finding:

- Review should verify realistic inputs, invalid inputs, ordering conflicts, authorization or ownership constraints, persistence side effects, and how the route interacts with nearby routes. A route declaration and one 200 response do not prove the product behavior.

## Manual QA stops too early

Bad approval:

- "I clicked through the happy path once and did not see an error."

Correct finding:

- Manual QA should exercise the acceptance checks, one relevant failure path or edge case, and the observable state after the interaction. If deeper coverage is not practical, review must record what remains unverified instead of treating the slice as fully proven.
