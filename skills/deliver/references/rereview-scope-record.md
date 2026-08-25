# Deliver Rereview Scope Record

Use this record only for repairs authorized during `$deliver` final review. Create `tasks/tmp/review-deliver-final-<plan-key>.rereview.json` before starting a repair rereview. For repairs imported from a fixed remediation packet, create every action before the first post-repair review, including when that review will be the ordinary mandatory full-branch review.

For every record, set `schema_version: 3`. Schema v2 records and records that mix the retired and current risk-flag keys fail closed.

For every repair action, record:

- `finding_id`
- a concise `repair_boundary`
- `approved_contract_basis` with exactly `effect` and `source`
- all nine Boolean `risk_flags`
- the validator-derived `required_scope`
- a concise `scope_rationale`

The required risk flags are:

- `architecture_or_trust_boundary`
- `cross_process_or_async_completion`
- `irreversible_mutation`
- `user_visible_output_or_diagnostics`
- `fallible_output_after_irreversible_mutation`
- `changes_approved_public_contract`
- `broad_security_or_data_integrity`
- `isolation_unproven`
- `new_material_finding`

Set `approved_contract_basis.effect` to `none`, `restore`, `change`, or `uncertain`, and set `source` to a non-empty evidence or approval citation. `change` means changing, expanding, withdrawing, or otherwise revising the approved caller-visible contract. `restore` means bringing the implementation back into agreement with a pre-repair approved contract without changing that contract. The non-empty `source` is the structural support required for a restoration; the validator does not attempt semantic citation parsing.

Set `changes_approved_public_contract` to true if and only if `effect` is `change`. For `uncertain`, keep that Boolean false and set `isolation_unproven` to true, which independently derives `full`. A supported `restore` remains `targeted` unless another full-review flag applies.

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

An ordinary mandatory full-branch review performed after fixed-packet repairs may be recorded as the grouped repair round when it covers every action; its `full` scope satisfies any validator-derived targeted or full action scope. A qualifying attested review imported as the initial round happened before repair and cannot serve this second purpose, so it still requires a separate post-repair round at the derived scope.

When that ordinary review is broader than an all-targeted action set, name its exact `round_id` explicitly during complete-phase validation:

```bash
python3 <deliver-skill-root>/scripts/validate_rereview_scope.py tasks/tmp/review-deliver-final-<plan-key>.rereview.json --phase complete --ordinary-post-repair-full-round <round-id>
```

The option is fail-closed: it is valid only during complete phase, the named round must exist with `full` scope, and that round must cover every recorded action. Do not use it for an ordinary repair rereview merely to inflate a targeted derived scope.

Resolve `<deliver-skill-root>` to the directory containing the loaded Deliver `SKILL.md` and execute this bundled validator in place. Do not copy the validator into the target repository or include a copied validator in the target diff.
