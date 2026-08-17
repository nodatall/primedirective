# Frozen Historical Evidence And Expected Behavior

Source: `tasks/merge-review-deliver-repo-sweep-swarm-nitpick.md`, Round 1 and its validation log.

- `MR-002` evidence: a corrupt `.last-session-update` caused `scripts/prime-directive-session-update.sh` to print a Bash arithmetic error, violating its silent best-effort behavior. Expected repair: sanitize non-digit or empty throttle content before subtraction. Expected proof: the corrupt-throttle probe emits no stderr.
- `MR-003` evidence: `scripts/prime-directive-codex-preflight.sh` called an updater that always backgrounded work, so it could return before the refresh and reinstall had completed. Expected repair: an explicit foreground mode used by Codex preflight, while the default invocation stays backgrounded. Expected proof: preflight returns only after the deterministic fake pull completes and the throttle file exists.

The historical permanent CI probes were added in `2e0c01916bebceca619f1b209a101e591ebfd07d`: write `not a number` to the throttle and require empty stderr; remove the throttle, run Codex preflight, and require the throttle file to exist on return. The supplied shell probes preserve those assertions and replace live git timing with a deterministic fake-git delay.
