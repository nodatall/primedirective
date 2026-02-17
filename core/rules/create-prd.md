---
description:
globs:
alwaysApply: false
---
# Rule: Generating a Product Requirements Document (PRD)

## Goal

To guide an AI assistant in creating a detailed Product Requirements Document (PRD) in Markdown format, based on an initial user prompt. The PRD should be clear, actionable, and suitable for a junior developer to understand and implement the feature.

## Process

1.  **Receive Initial Prompt:** The user provides a brief description or request for a new feature or functionality.
2.  **Run Interrogation Output (Required):** Before drafting, produce a short pre-PRD section with:
    - `Assumptions` (current best guesses)
    - `Unknowns` (facts missing)
    - `Business Decisions Needed` (choices product owner must make)
    - `Risk Register` (High / Medium / Low)
3.  **Ask Clarifying Questions:** Before writing the PRD, the AI *must* ask clarifying questions to gather sufficient detail. The goal is to understand the "what" and "why" of the feature, not necessarily the "how" (which the developer will figure out).
4.  **High-Risk Gate:** If any `High` risk remains in the interrogation output, the AI must ask at least one direct clarifying question that reduces that risk before generating the PRD.
5.  **Generate PRD:** Based on the initial prompt and the user's answers to the clarifying questions, generate a PRD using the structure outlined below.
6.  **Contract Preservation Gate (Required):** If the user provides exact technical contracts (schema fields/types, enum values, API call order, constraints, indexes), preserve them as normative content. Do not replace exact contracts with a summarized variant.
7.  **Appendix Injection (Required when contracts exist):** Add appendices that capture exact contracts verbatim or near-verbatim:
    - `Appendix A: Data Model Contracts`
    - `Appendix B: External API Contracts`
    - `Appendix C: Event/State Enums and Constraints`
    - `Appendix D: Invariants and Ordering Guarantees`
8.  **Save PRD:** Save the generated document as `prd-[feature-name].md` inside the `/tasks` directory.

## Clarifying Questions (Examples)

The AI should adapt its questions based on the prompt, but here are some common areas to explore:

*   **Problem/Goal:** "What problem does this feature solve for the user?" or "What is the main goal we want to achieve with this feature?"
*   **Target User:** "Who is the primary user of this feature?"
*   **Core Functionality:** "Can you describe the key actions a user should be able to perform with this feature?"
*   **User Stories:** "Could you provide a few user stories? (e.g., As a [type of user], I want to [perform an action] so that [benefit].)"
*   **Acceptance Criteria:** "How will we know when this feature is successfully implemented? What are the key success criteria?"
*   **Scope/Boundaries:** "Are there any specific things this feature *should not* do (non-goals)?"
*   **Data Requirements:** "What kind of data does this feature need to display or manipulate?"
*   **Design/UI:** "Are there any existing design mockups or UI guidelines to follow?" or "Can you describe the desired look and feel?"
*   **Edge Cases:** "Are there any potential edge cases or error conditions we should consider?"

## PRD Structure

The generated PRD should include the following sections:

1.  **Introduction/Overview:** Briefly describe the feature and the problem it solves. State the goal.
2.  **Goals:** List the specific, measurable objectives for this feature.
3.  **User Stories:** Detail the user narratives describing feature usage and benefits.
4.  **Functional Requirements:** List the specific functionalities the feature must have with stable IDs (`FR-1`, `FR-2`, ...). Use clear, concise language (e.g., "The system must allow users to upload a profile picture.").
5.  **Acceptance Criteria:** For each functional requirement ID, define explicit pass/fail checks so implementation can be verified without ambiguity.
6.  **Non-Goals (Out of Scope):** Clearly state what this feature will *not* include to manage scope.
7.  **Design Considerations (Optional):** Link to mockups, describe UI/UX requirements, or mention relevant components/styles if applicable.
8.  **Technical Considerations (Optional):** Mention any known technical constraints, dependencies, or suggestions (e.g., "Should integrate with the existing Auth module").
9.  **Success Metrics:** How will the success of this feature be measured? (e.g., "Increase user engagement by 10%", "Reduce support tickets related to X").
10. **Open Questions:** List any remaining questions or areas needing further clarification.
11. **Appendices (Required when technical contracts are provided):** Exact schema/API/enum/invariant contracts must be listed explicitly so implementation has zero ambiguity.

## Target Audience

Assume the primary reader of the PRD is a **junior developer**. Therefore, requirements should be explicit, unambiguous, and avoid jargon where possible. Provide enough detail for them to understand the feature's purpose and core logic.

## Output

*   **Format:** Markdown (`.md`)
*   **Location:** `/tasks/`
*   **Filename:** `prd-[feature-name].md`

## Final instructions

1. Do NOT start implementing the PRD
2. Make sure to ask the user clarifying questions
3. Take the user's answers to the clarifying questions and improve the PRD
4. After task generation is completed for this PRD, run the post-generation review pass in `rules/improve-plan.md` to refine the PRD + task plan before implementation begins.
5. Never downgrade explicit user-provided contracts into looser summaries; keep exact contracts in appendices even if main sections are simplified for readability.
