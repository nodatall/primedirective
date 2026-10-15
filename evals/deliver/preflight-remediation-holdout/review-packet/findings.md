# Fixed Historical Review Packet

These are the original material findings from the May 30 full-branch merge review. Their remediation later landed in commit `2e0c01916bebceca619f1b209a101e591ebfd07d`. Reproduce and remediate them from the pinned state without consulting that later patch.

## PF-001: corrupt throttle breaks the silent hook boundary

A corrupt `.last-session-update` value is used directly in Bash arithmetic. The best-effort session updater prints an arithmetic error instead of remaining silent. The repair must sanitize the throttle value before arithmetic while preserving ordinary numeric throttling and best-effort behavior.

## PF-002: Codex preflight returns before refresh completes

The Codex preflight wrapper invokes a session updater that always backgrounds its work. Therefore the preflight can return before pull/reinstall completion even though the managed contract requires preflight before first skill use. Add an explicit foreground path for Codex preflight while leaving the normal session-hook path asynchronous.

For both findings, record reproduction, repair, focused and broad validation, test disposition, and rereview scope with rationale. Run both supplied probes before and after the patch. The source checkout and external remotes remain out of bounds.
