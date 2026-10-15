# Fixed Remediation Review Packet

The pre-packet implementation and public validation have already been frozen. Investigate and disposition each finding below, repair every reproduced contract defect, decide what permanent coverage has durable value, and use the narrowest trustworthy fresh rereview allowed by the supplied Deliver contract. Record finding IDs, reproduction and verification evidence, test disposition and rationale, rereview scope and rationale, review actions, and timing. Do not inspect evaluator-owned files.

## RF-001: chronological limited selection

Raw string ordering can select `2026-01-01T00:00:00Z` before `2026-01-01T00:30:00+01:00`, even though the offset timestamp is 30 minutes earlier. Reproduce through `retry-failed --limit 1 --dry-run --json`; equal instants must still break ties by job ID, and unusable eligible timestamps must enter the status-2/no-write boundary.

## RF-002: normal malformed-input and mutation boundaries

Investigate these related public-entrypoint cases:

- validation accepts `history: null`, but naïve mutation calls `.append()` on `None`;
- container-valued `status` can raise during membership testing;
- invalid UTF-8 can escape JSON error normalization;
- JSON `version: true` compares equal to integer `1` in Python and can be mutated;
- an escaped lone-surrogate job ID can fail while reporting after a real retry has persisted.

All malformed or operationally unreportable state must return status 2, keep stdout clean, avoid a traceback, and preserve original bytes. `history: null` is validator-accepted and should behave like absent history.

## RF-003: rare decoder and serialization limits

A 5,000-digit JSON integer can raise a decoder `ValueError`. A valid envelope with an eligible job and an unknown top-level list nested to depth 1,500 can load but raise `RecursionError` during atomic JSON serialization. Reproduce the latter with `deep-structure-probe.py`. Both failures are within the promised diagnostic/no-write boundary. Decide separately whether the repair needs durable test-suite cases or preserved one-run proof.

## RF-004: helper-only boolean concern

A direct call to a reusable positive-integer converter may accept Python `True`, while the public `argparse` CLI passes only strings. Determine whether this is reachable through a supported path and whether any production change or permanent test would provide durable protection.
