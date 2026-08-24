# Deliver Rereview Scope Record

Use this record only for repairs authorized during `$deliver` final review. Create `tasks/tmp/review-deliver-final-<plan-key>.rereview.json` before starting a repair rereview.

For every record, set `schema_version: 2`.

For every repair action, record:

- `finding_id`
- a concise `repair_boundary`
- all nine Boolean `risk_flags`
- the validator-derived `required_scope`
- a concise `scope_rationale`

The required risk flags are:

- `architecture_or_trust_boundary`
- `cross_process_or_async_completion`
- `irreversible_mutation`
- `user_visible_output_or_diagnostics`
- `fallible_output_after_irreversible_mutation`
- `public_contract`
- `broad_security_or_data_integrity`
- `isolation_unproven`
- `new_material_finding`

The validator derives `full` when any direct full-review flag is true or when `fallible_output_after_irreversible_mutation` is true. Set that ordered-failure flag when the repair changes or protects a failure boundary where a fallible user-visible output or diagnostic step runs after irreversible mutation. The flag may be true only when both `irreversible_mutation` and `user_visible_output_or_diagnostics` are true. Mere mutation plus reporting does not require the flag when their ordering and failure boundary are unchanged. Otherwise the validator derives `targeted`.

Before rereview, leave `rounds` empty and run:

```bash
python3 <deliver-skill-root>/scripts/validate_rereview_scope.py tasks/tmp/review-deliver-final-<plan-key>.rereview.json --phase plan
```

After rereview, add each executed round with `round_id`, `reviewed_finding_ids`, and `scope`, then run:

```bash
python3 <deliver-skill-root>/scripts/validate_rereview_scope.py tasks/tmp/review-deliver-final-<plan-key>.rereview.json --phase complete
```

Do not start the repair rereview unless the plan-phase command passes. Do not mark the final review complete unless the complete-phase command passes. For a grouped round, the validator requires the widest scope derived for its listed actions.
