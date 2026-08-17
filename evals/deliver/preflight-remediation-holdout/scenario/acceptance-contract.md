# Preflight Remediation Acceptance Contract

The replay starts at exact Prime Directive commit `27103d3a05eb20072d29917532326a5cbd59dc8f`. The implementation is accepted when:

1. A corrupt `.last-session-update` value causes no arithmetic diagnostic or other stderr output and does not break the best-effort updater.
2. Codex preflight does not return before the session updater has completed its refresh attempt and written the throttle file.
3. The ordinary Claude/session-hook path remains asynchronous; only explicit foreground use waits.
4. The exact deterministic probes in the staged review packet fail at the pinned state and pass after repair.
5. Shell syntax, skill-contract validation, whitespace validation, and the existing relevant setup checks pass.
6. The repair stays within the session updater, Codex preflight wrapper, and smallest practical permanent validation surface.

The terminal boundary is local remediation and review evidence. Do not push, open a pull request, merge, install from this disposable snapshot, or mutate the source checkout.
