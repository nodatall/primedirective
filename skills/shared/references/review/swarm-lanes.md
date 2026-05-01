# Swarm Lanes

Use this reference only when a review or repo sweep explicitly requests parallel specialized review lanes, such as `$repo-sweep --swarm`.

The lanes are read-only discovery lanes. They do not patch, refactor, or approve their own findings. The main agent owns deduplication, evidence checks, severity, disposition, repair decisions, and final reporting.

## Lanes

### Intent and Regression

Look for behavior that contradicts the repo's apparent product intent, existing tests, public interfaces, persisted data shape, migration history, or main user/system journeys.

### Security and Privacy

Look for auth, authorization, CORS, CSRF, secret handling, PII exposure, unsafe defaults, data exfiltration, public mutation endpoints, destructive paths, and trust-boundary failures.

### Performance and Reliability

Look for hot-path blocking work, unbounded fan-out, missing timeouts, retry storms, queue/idempotency gaps, scale assumptions, memory/disk coupling, slow startup, and brittle deploy/runtime wiring.

### Contracts and Coverage

Look for schema/API contract drift, missing migration coverage, mock-only tests, display-only behavior, unexercised acceptance paths, weak fixtures, and verification gaps around critical flows.

## Output Contract

Each lane returns only evidence-backed candidate findings:

- Short title.
- Files, commands, logs, probes, or artifacts inspected.
- Candidate severity and confidence.
- Evidence and disconfirming evidence checked.
- Suggested disposition using `fix`, `needs human decision`, `residual risk`, or `no action`.

Lanes should also return a short `looks bad but is fine` list when they investigated a suspicious pattern and found a real guard.

## Main-Agent Merge Rules

The main agent must:

1. Deduplicate overlapping findings.
2. Prefer runtime/probe evidence over static inference when both are available.
3. Downgrade or discard findings without reachable code paths or concrete evidence.
4. Preserve high-confidence dissent when lanes disagree and explain the uncertainty.
5. Convert accepted findings into the shared finding disposition shape before the report or loop queue.
