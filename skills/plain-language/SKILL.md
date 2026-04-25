---
name: plain-language
description: Use when the user asks for a plainer, simpler, shorter, or more direct explanation, rewrite, summary, restatement, or answer. Produces concrete full-sentence explanations that lead with the main point and avoid needless jargon.
---

# Plain Language Skill

Load `skills/shared/references/plain-language.md` before answering.

## Activation

Invoke explicitly with `$plain-language`.

Also use this skill when the user asks for:

- plain language
- plainer wording
- a simpler explanation
- a shorter explanation
- a direct restatement
- full sentences instead of bullets

## Workflow

1. Identify the main point the user needs.
2. Strip away abstractions that do not change the meaning.
3. Answer using `skills/shared/references/plain-language.md`.
4. Stop when the explanation is clear. Do not add caveats, examples, or extra structure unless they prevent misunderstanding.

## Output

Default to 2-5 short full sentences.

Use bullets only when the user asks for them or when a list is clearly easier to read.

Do not mention the skill, the reference, or the rewrite process.
