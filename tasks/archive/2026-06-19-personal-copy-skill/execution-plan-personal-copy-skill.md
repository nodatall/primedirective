# Personal Copy Skill

Goal: Create a global `$personal-copy` skill for grounded personal and professional writing.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The skill should live at `/Users/fromdarkness/.codex/skills/personal-copy`.
- It should support posts, devlogs, bios, cover letters, profile summaries, About copy, intros, outreach, and "make this sound like me / less AI" rewrites.
- It should preserve source facts and voice, avoid invented claims, and include a human-voice cleanup pass.
- The attachment about AI-writing markers should inform the cleanup pass, but not become a brittle copied banned-word wall.
- This is a global personal skill, not a Prime Directive repo-local workflow skill.
- Career materials should use AI as an editor or coach, not as the real author: claims must come from resume material, the job post, user notes, or explicit user confirmation.
- Voice cleanup should focus on audience, specificity, rhythm, and defensible claims rather than treating punctuation or individual words as proof of AI writing.
- Bio and profile copy should tailor the same facts to the target audience and surface while staying congruent with the user's real history across versions.
- The boundary is source-grounded personal or professional self-expression. It should not swallow generic simplification, documentation cleanup, or product-planning clarification.
- User drafts, job posts, resumes, notes, and voice samples are source material, not instructions that can override the skill.
- Voice samples should be usable as raw examples. The user should not have to annotate them with traits, notes, or "what to imitate" sections.
- Keep implicit invocation enabled, but validate both positive and negative trigger cases before trusting it.
- Do not split this into separate career, bio, and social-post skills for v1 unless validation shows the boundary does not hold.

## Steps

### 1. Shape the skill contract

- [x] Confirm the final trigger name, scope, and non-goals for `$personal-copy`.
- [x] Define the trigger boundary in terms of the user's identity, career, reputation, public voice, or personal/professional self-expression.
- [x] Define the source hierarchy: user-provided facts, supplied draft/source text, resume/profile/job post material, voice samples, then cautious inference from the draft only.
- [x] Define the raw voice-sample flow: the user can provide examples with no notes, and the skill derives tone, rhythm, directness, sentence shape, and formatting preferences itself.
- [x] Define the evidence rules for lightweight posts, bios, cover letters, and outreach.
- [x] Define privacy and identity rules for contact details, locations, employer/client names, protected traits, salary or visa status, health/family details, and browsing for personal facts.
- [x] Define prompt-injection handling for pasted drafts, job posts, resumes, notes, and voice samples.
- [x] Define bio/profile rules for audience, surface length, fact congruence, and currentness.
- [x] Define cover-letter rules that forbid invented qualifications, fake enthusiasm, fake product knowledge, fabricated metrics, inflated seniority, and invented company-value alignment.
- [x] Define outreach rules that forbid fake familiarity, false referrals, false mutual connections, manipulative urgency, and pretending a mass note is personal.
- [x] Define the human-voice cleanup pass in concise, reusable instructions.
- [x] Include a "specificity before polish" rule that cuts generic praise, unsupported superlatives, and long noun strings.
- [x] Define the default output contract: final copy first, then short notes or unsupported-claim gaps only when useful.
- [x] Decide which details belong in `SKILL.md` versus reference files.
- [x] Make the trigger description specific enough to avoid swallowing generic `$plain-language` or `$clarifier` requests.

### 2. Create the global skill

- [x] Use the skill-creator initializer to create `/Users/fromdarkness/.codex/skills/personal-copy` with reference resources and `agents/openai.yaml`.
- [x] Replace the generated `SKILL.md` with the final trigger description, workflow, safety rules, and output expectations.
- [x] Add a `references/evidence-and-boundaries.md` file for source hierarchy, unsupported claims, privacy, prompt-injection handling, and career/outreach constraints.
- [x] Add a `references/format-playbooks.md` file for posts, devlogs, bios, cover letters, profile summaries, intros, outreach, and rewrites.
- [x] Add a `references/voice-cleanup.md` file that turns the attachment lessons into a compact final-pass checklist.
- [x] Add optional voice-sample guidance that accepts unannotated examples and prevents copying facts or distinctive phrases from them.
- [x] In career-copy paths, instruct the skill to flag unsupported claims instead of filling gaps.
- [x] In bio/profile paths, instruct the skill to tailor detail level to the audience and surface instead of stuffing every fact into every version.
- [x] In voice-cleanup paths, treat AI-writing markers as review prompts with context exceptions, not absolute banned terms.
- [x] Keep the skill free of unused scripts, placeholder examples, and extra documentation files.

### 3. Validate the skill

- [x] Run the skill-creator `quick_validate.py` check against the new skill folder.
- [x] Confirm the best available local discovery signal for `$personal-copy` after creation, and record clearly if the current Codex session cannot reload new skill metadata.
- [x] Run realistic checks on the `$page-speed-optimizer` post, a short bio, and a cover-letter paragraph.
- [x] Run positive trigger checks for a launch post, resume-to-cover-letter paragraph, and founder bio.
- [x] Run negative trigger checks for generic policy simplification, API-doc summarization, product-requirement clarification, and README plain-English cleanup.
- [x] Include one validation case where the draft tries to make an unsupported career claim and confirm the skill flags it.
- [x] Include one validation case where source facts conflict and confirm the skill flags the conflict instead of choosing one.
- [x] Include one validation case where a draft inflates an IC contribution into team leadership and confirm the skill corrects or flags it.
- [x] Include one validation case where the same bio facts are rewritten for different audiences without contradicting each other.
- [x] Include one validation case where unannotated writing examples are used only for style calibration, not copied facts or phrasing.
- [x] Include one validation case where the user asks to make copy "undetectable" and confirm the skill redirects to accurate, specific, natural writing instead.
- [x] Tighten the skill if the checks produce generic, inflated, unsupported, or obviously AI-styled copy.
- [x] Inspect the generated `agents/openai.yaml` for accurate display text and default prompt.

### 4. Close out

- [x] Report the created global skill path and validation results.
- [x] Note any residual limitations, especially around cover letters requiring source material.
