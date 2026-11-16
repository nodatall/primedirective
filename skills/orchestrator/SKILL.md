---
name: orchestrator
description: Run this chat as an orchestrator that delegates leading ! tasks to subagents and selects each worker's model and reasoning effort from current runtime capabilities. Use when the user invokes $orchestrator or asks for this chat-level delegation convention.
---

# Orchestrator

Keep the main chat responsible for understanding the request, assigning work, checking results, and answering the user. Delegate implementation or investigation through focused subagents when the user prefixes a task with `!`.

## Chat mode

`$orchestrator` enables this convention for the current chat until the user turns it off. A bare activation acknowledges the mode briefly and waits for a task; it does not create a worker. Activation authorizes choosing available worker models and reasoning levels for delegated tasks, subject to explicit user model or budget constraints. Keep the parent chat's model unchanged.

- A top-level user message beginning with `!task` or `! task` delegates that task. Strip the marker when making the brief. Apply the same rule to a task supplied alongside `$orchestrator`.
- A bare `!` delegates the most recently agreed, unambiguous task. If there is no clear task, ask what to delegate before spawning.
- Ordinary conversation stays with the parent unless the user or an applicable workflow explicitly requests delegation. A literal `!` in quoted text, fenced or inline code, a Markdown image, or punctuation inside a message is not a delegation trigger.
- `$orchestrator off` or an equivalent request ends this convention. If workers are still active, distinguish ending the convention from a request to cancel their work; honor explicit cancellation by interrupting the affected agents.
- Keep mode state, active task identifiers, ownership, and pending checks in the chat's continuation context when it is compacted. This is a chat convention; do not install a global `!` hook or change unrelated chats or Codex defaults.

On activation, explain the controls in one sentence: “Orchestrator mode is on. Prefix a task with `!` to delegate it; I’ll choose the worker settings and check the result.”

## Choose a worker

The parent Codex orchestrator selects both the model and reasoning effort directly, using the task context and live runtime metadata. Do not delegate this selection to another agent or model, or introduce a separate routing service or dependency.

Discover the choices exposed by the live agent tool or runtime model catalog. Use their current capability descriptions, supported reasoning levels, context limits, and any available latency or cost information. Honor user overrides and budget constraints first. Refresh this information when the runtime exposes changes or a selection is rejected. Do not maintain model names, version rankings, or a model-to-task lookup table in this skill.

Make a fresh suitability judgment for each assignment:

- Assess the task's ambiguity, reasoning demands, required tools and context, dependencies, consequences of mistakes, and the checks that can establish success. Word count and file count alone do not establish difficulty.
- Among the available models that can reliably meet those needs, prefer lower latency and cost when the runtime provides evidence for that comparison. Clear mechanical work can use a lighter worker; uncertain debugging, security, design judgment, or cross-system behavior calls for stronger relevant capabilities.
- Choose reasoning effort independently of model choice, using only levels supported by that model. Match it to the task's uncertainty and consequences, and reassess it when evidence warrants deeper investigation.

Newly exposed models are eligible through the same assessment without editing this skill. Compare their documented suitability for the task; a newer name or version does not establish that they are better, faster, or cheaper. Do not invent capability or pricing facts from a model identifier. If the live catalog lacks information needed to make the choice, consult current official metadata when available; otherwise use a supported default or inherited route within the user's constraints and disclose the selection uncertainty. If the task itself is unclear, gather targeted context or assign bounded discovery before assigning edits.

With `collaboration.spawn_agent`, set `model` and `reasoning_effort` explicitly for deliberate routing and use `fork_turns: "none"`. Write a self-contained brief because that worker will not receive the conversation. In this tool, omitting `fork_turns` or setting it to `"all"` inherits the parent's settings and does not allow overrides. Use full-history inheritance only when the task actually needs it, omit overrides, and describe the route as inherited. On other hosts, use the equivalent options actually supported by their agent tool.

Before spawning, give a short dispatch update naming the task, selected model and reasoning, and the practical reason supported by the task and current runtime metadata. Do not invent settings or claim a worker used a model the tool did not select. If model overrides are unavailable, disclose that limitation and use the supported inherited route. If agent tools are unavailable, say delegation could not run and complete the task locally when permitted.

## Assign and coordinate

Start with one worker per delegated task. Split only when there are independent outcomes worth the coordination cost. Parallel read-only investigations are useful; parallel edits require separate file ownership and no dependency on each other's unfinished work. Serialize overlapping edits, shared config changes, and integration steps. The parent owns dispatch; workers should not recursively delegate by default.

Give each worker the minimum context needed to finish correctly:

- The outcome, relevant decisions from the conversation, and concrete completion criteria.
- The absolute repository or working path, relevant files or symbols, and where to read applicable `AGENTS.md` and design or architecture instructions.
- The surfaces it may edit, existing changes to preserve, shared-workspace ownership, and dependencies that must finish first.
- Required skills or workflow constraints and the checks or UI evidence needed to establish completion.
- The scope of authorized side effects. Request a report of changes, verification actually run, remaining uncertainty, and any blocker requiring the parent's judgment.

Do not send the whole backlog or irrelevant conversation. Include necessary constraints in the brief rather than assuming that `fork_turns: "none"` preserves them. Workers must inspect current sources and obey applicable project instructions. Assign work within existing authorization; `!` does not independently authorize publishing, sending messages, deployments, purchases, commits, or pushes.

When a delegated request invokes another skill, read its owner instructions and preserve its workflow, approval points, model requirements, and worker topology. Keep its orchestration in the parent and assign its worker-sized tasks from there. For example, `$deliver` still owns its plan and review process. This skill's selection guidance is a default for its own tasks, not an override of another skill's explicit requirements. Do not start an extra planning or review workflow merely because delegation was requested.

Track active agents and route steering to the worker that owns the task. A new independent `!` request may add work; a correction or cancellation updates the existing assignment. Do not launch a competing writer for the same files. Continue independent parent work while agents run and wait for every result needed by the user's request before claiming completion.

## Check and finish

Inspect the actual result and relevant diff or artifact. Check acceptance criteria against evidence, not the worker's completion claim. Run the appropriate focused validation when the evidence is missing, stale, or insufficient; verify rendered UI when the result depends on UI behavior. Integrate dependent changes only after their prerequisites are ready.

After a worker failure, classify the cause before retrying. Missing permissions, environment, tools, or user decisions need those issues addressed; more reasoning does not supply them. If a fast worker encounters material ambiguity, expands scope, or fails focused verification because of a reasoning or implementation error, preserve its useful work and route the unresolved slice to a stronger worker with the failure evidence. Do not repeatedly retry the same cheap route or run competing repairs. Stop retries when a concrete blocker requires user input or an external change, and report it.

Return the outcome, meaningful verification, and any material limitation concisely. Keep orchestration chatter out of the final answer unless it explains a limitation or the user asks about routing.

For Codex configuration background, see the [official subagents guide](https://learn.chatgpt.com/docs/agent-configuration/subagents). The live tool schema determines which spawn settings this chat can use.
