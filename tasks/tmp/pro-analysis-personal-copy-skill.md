# Pro Analysis Memo: Personal Copy Skill

plan_key: personal-copy-skill
target_plan: `tasks/execution-plan-personal-copy-skill.md`
context_bundle: `tasks/tmp/pro-context-personal-copy-skill.md`
research_memo: `tasks/tmp/research-plan-personal-copy-skill.md`

## Context Bundle Summary

Sent a curated 1,451-word bundle containing:

- the current Deliver execution plan
- the completed deep-research findings
- local skill-creator constraints
- the attachment lessons as a summarized cleanup signal
- focused questions about scope, guardrails, validation, and skill file layout

Excluded:

- unrelated repo files and task artifacts
- private browser tabs
- secrets, env files, API keys, customer data, and personal resume/job-history files beyond the user-provided attachment summary already discussed in this thread

## Browser Run Evidence

- driver used: `chrome`
- browser surface: user's normal Chrome profile through the Chrome control surface
- ChatGPT surface: `https://chatgpt.com/?temporary-chat=true`
- initial browser finding: an existing ChatGPT tab had unsent user draft text, so it was left untouched
- submission surface: clean Temporary Chat in a new regular Chrome tab
- selected model label: `Pro Extended`
- model-selection verification: opened the visible picker from the `Extra High` button, selected `Pro Extended`, then verified the visible composer button changed to `Pro Extended` before submission
- submission method: pasted/filled the curated context bundle into the composer; ChatGPT displayed it as `Pasted text.txt`
- response completion evidence: final answer displayed `Thought for 3m 55s`, stop control disappeared, and answer action controls appeared
- capture method: DOM extraction from the completed assistant message

## Pro Findings Ledger

| finding_id | Pro claim | local verification evidence | disposition | disposition reason |
| --- | --- | --- | --- | --- |
| PF1 | Add a post-creation path/discovery check because public Codex docs and local skill paths differ. | Local global skills are under `/Users/fromdarkness/.codex/skills`; OpenAI docs currently reference `$HOME/.agents/skills`; the plan already chose the local path but only had `quick_validate.py`. | adopted | Added validation to confirm local discovery/listing after creation. |
| PF2 | Tighten the trigger boundary against `$plain-language` and `$clarifier`. | Existing plan had a generic avoidance item; Pro gave concrete negative boundaries. | adopted | Added identity/career/reputation/public-voice boundary and negative trigger validation. |
| PF3 | Add an explicit source hierarchy. | Research memo already supports source-backed claims; plan did not spell out priority order. | adopted | Added a source-hierarchy checkbox and moved it into planned `evidence-and-boundaries.md`. |
| PF4 | Add anti-prompt-injection handling for pasted source material. | The skill will process arbitrary drafts, job posts, resumes, notes, and voice samples. | adopted | Added source-material-as-content rule and prompt-injection handling checklist item. |
| PF5 | Add privacy and identity guardrails. | The skill scope includes career/profile/outreach copy where personal details can be invented or overexposed. | adopted | Added privacy/identity checklist item and evidence reference scope. |
| PF6 | Strengthen cover-letter rules. | Research memo already supported defensible career-copy rules; Pro supplied concrete forbidden claims. | adopted | Added cover-letter rules for fake enthusiasm, fake product knowledge, fabricated metrics, inflated seniority, and invented alignment. |
| PF7 | Strengthen outreach rules. | Outreach was in scope but had no specific fraud/manipulation guardrails. | adopted | Added outreach rules against fake familiarity, referrals, mutual connections, and manipulative urgency. |
| PF8 | Add a detector-evasion redirect validation case. | Research memo explicitly rejected detector evasion but validation did not test the user wording. | adopted | Added an "undetectable" validation case that redirects to accurate, specific, natural writing. |
| PF9 | Add `references/evidence-and-boundaries.md`. | Evidence, privacy, prompt-injection, and career/outreach constraints cross multiple formats and would bloat `SKILL.md`. | adopted | Added the third reference file to the plan. |
| PF10 | Add negative trigger validation. | Current validation focused on positive output quality only. | adopted | Added negative cases for policy simplification, API-doc summarization, product-requirement clarification, and README plain-English cleanup. |
| PF11 | Add contradiction and inflated-claim stress tests. | Existing plan had unsupported-claim and bio-congruence checks but no direct conflict/inflation cases. | adopted | Added conflicting-facts and IC-to-leadership-inflation validation cases. |
| PF12 | Define the output contract more tightly. | Attachment and research both warn against overformatted AI-looking output. | adopted | Added default output contract: final copy first, notes only when useful. |
| PF13 | Do not split into multiple skills yet. | The boundary is coherent if restricted to source-grounded personal/professional copy. | deferred | Added a v1 decision note to avoid premature split unless validation shows the boundary fails. |
| PF14 | Do not disable implicit invocation by default. | Natural prompts like "make this sound like me" should trigger the skill. | rejected | Kept implicit invocation enabled, but added boundary and validation checks. |
| PF15 | Make repo-style closeout conditional. | The exact Deliver implementation instruction is mandated by the Deliver plan format. Implementation may still need to report global skill artifacts separately. | partially adopted | Did not change the Deliver instruction; the closeout phase already reports global path and validation limitations. |

## Conflict Reconciliation

- Public docs vs local skill path: keep `/Users/fromdarkness/.codex/skills/personal-copy` because the live local environment discovers user skills there; add a discovery/listing validation step to catch drift.
- Pro suggestion to condition repo-style closeout: do not edit the required Deliver implementation instruction. Keep the workflow contract intact and use the closeout checklist to report global skill files and validation.
- Implicit invocation: reject disabling it by default. The better control is narrower trigger text plus explicit negative trigger checks.
- Scope split: defer. A single skill remains coherent if implementation centers on source-grounded personal/professional copy.

## Artifact Delta

Changed `tasks/execution-plan-personal-copy-skill.md`:

- `What We Know`: added boundary, prompt-injection, implicit-invocation, and no-premature-split decision notes
- Step 1: added trigger boundary, source hierarchy, privacy/identity, prompt-injection, cover-letter, outreach, and output-contract work
- Step 2: added `references/evidence-and-boundaries.md`
- Step 3: added discovery validation, positive/negative trigger checks, contradiction/inflation stress tests, and detector-evasion redirect validation

No external source-backed Pro claim required new web research beyond the completed deep-research memo and already-opened OpenAI Codex skill docs.

## Pro Synthesis Completion Stamp

pro_result_read: yes
pro_browser_run: yes
pro_model_selected: yes
findings_reconciled: yes
artifact_changes_applied: yes
unresolved_blockers: none
pro_synthesis_complete: yes
