# Repo Sweep Go-Live Readiness

Use this reference when `$repo-sweep` reviews a deployable web app, API, worker, upload flow, websocket/realtime feature, background job, database-backed service, or third-party integration.

For local-only CLIs, libraries, prototypes, and non-deployable tools, mark irrelevant items `not applicable` with a short reason.

Check:

- Load and capacity evidence: load/stress test command, known traffic limit, rate-limit behavior, and the highest-risk bottleneck if no load test exists.
- Horizontal scale assumptions: server-memory sessions, in-memory queues, in-memory rate limits, websocket state, local disk state, and whether multiple app instances would preserve behavior.
- File uploads and static assets: uploads should not depend on ephemeral app-server disk for durable storage, and large/static assets should have an object-storage/CDN path when traffic volume warrants it.
- Background work: email sending, webhooks, image/video processing, AI calls, report generation, and other slow tasks should not block latency-sensitive API routes unless the synchronous behavior is explicitly acceptable.
- Queue and worker behavior where background tasks exist: retry policy, dead-letter/failure visibility, idempotency, and whether one slow task can block unrelated work.
- Database production readiness: indexed join/filter columns for hot paths, transactions for multi-step writes, migration race safety, test/seed/reset isolation, backup existence, and restore-test evidence or a residual-risk note.
- HTTP/runtime safety: compression for large responses, health checks, graceful shutdown, bounded request/body sizes where relevant, and no deploy-time behavior that can corrupt shared state.
- Outbound dependency resilience: connection timeouts, bounded retries, circuit breakers or load-shedding where relevant, fallback/degradation behavior, and clear failure logging.
- Logs and incident readiness: logs should not be local-disk-only for deployable services, errors should be alertable, and common incidents should have a runbook or at least an explicit residual-risk note.

Report each applicable item as `verified`, `finding`, `not applicable`, or `residual risk`. Do not convert every missing launch-hardening item into an automatic fix; stop for product, cost, infrastructure, data, or operational decisions.
