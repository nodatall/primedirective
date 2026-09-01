# Deliver Rereview Scope Record

Use this record only for repairs authorized during `$deliver` final review.

Create `tasks/tmp/review-deliver-final-<plan-key>.rereview.json` before the repair rereview starts. For a fixed remediation packet, record every repair before the first post-repair review, even when that review will be the normal full-branch review.

## Record Each Repair

Use `schema_version: 3`. Schema v2 and records that mix current and retired risk-flag names fail closed.

Each repair action must contain:

- `finding_id`
- `repair_boundary`: a short description of the pre-repair defect boundary changed or protected
- `approved_contract_basis` with exactly `effect` and `source`
- all nine Boolean `risk_flags`
- the validator-derived `required_scope`
- `scope_rationale`

The nine risk flags are:

- `architecture_or_trust_boundary`
- `cross_process_or_async_completion`
- `irreversible_mutation`
- `user_visible_output_or_diagnostics`
- `fallible_output_after_irreversible_mutation`
- `changes_approved_public_contract`
- `broad_security_or_data_integrity`
- `isolation_unproven`
- `new_material_finding`

## Record The Contract Basis

`approved_contract_basis.effect` is exactly `none`, `restore`, `change`, or `uncertain`.

`approved_contract_basis.source` must cite non-empty evidence or user approval. The validator checks that the field is present, not that the citation is semantically correct.

- `none`: the repair does not change or restore a caller-visible contract.
- `restore`: the repair returns behavior to a cited approved contract.
- `change`: the repair changes, expands, withdraws, or otherwise revises the approved caller-visible contract.
- `uncertain`: available evidence cannot prove whether the contract changes.

Set `changes_approved_public_contract` to true if and only if `effect` is `change`. For `uncertain`, keep it false and set `isolation_unproven` to true. A supported `restore` stays `targeted` unless another full-review flag applies.

## Derive Scope From The Old Boundary

Set every risk flag from the pre-repair defect boundary changed or protected, not only from the repaired code path.

The validator derives `full` from any direct full-review flag or from `fallible_output_after_irreversible_mutation`.

Set the ordered-failure flag only when a fallible user-visible output or diagnostic follows an irreversible mutation in that pre-repair boundary. It may be true only when both `irreversible_mutation` and `user_visible_output_or_diagnostics` are true. Mutation plus reporting does not require it when their order and failure boundary did not change. Without a full-review trigger, scope is `targeted`.

## Validate Before Rereview

Leave `rounds` empty and run:

```bash
python3 <deliver-skill-root>/scripts/validate_rereview_scope.py tasks/tmp/review-deliver-final-<plan-key>.rereview.json --phase plan
```

Do not start the repair rereview unless this passes.

## Validate After Rereview

Add every executed round with `round_id`, `reviewed_finding_ids`, and `scope`. Then run:

```bash
python3 <deliver-skill-root>/scripts/validate_rereview_scope.py tasks/tmp/review-deliver-final-<plan-key>.rereview.json --phase complete
```

Do not mark final review complete unless this passes. A grouped round must use the widest scope derived for its actions.

A normal full-branch review run after fixed-packet repairs may also be the grouped repair round when it covers every action. Its `full` scope can satisfy `targeted` or `full` actions. A qualifying packet review happened before the repairs, so it cannot close them.

When that normal review is broader than an all-targeted action set, name its exact `round_id`:

```bash
python3 <deliver-skill-root>/scripts/validate_rereview_scope.py tasks/tmp/review-deliver-final-<plan-key>.rereview.json --phase complete --ordinary-post-repair-full-round <round-id>
```

This option fails closed. Use it only in the complete phase for an existing `full` round that covers every action. Do not use it to widen a normal repair rereview.

Resolve `<deliver-skill-root>` to the folder containing the loaded Deliver `SKILL.md`. Run its validator in place. Do not copy the validator into the target repo or include a copy in the target diff.
