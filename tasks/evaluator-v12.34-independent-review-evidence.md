# V12.34 Independent Review Evidence

This note records evidence reported by the fresh review agent
`/root/evaluator_v134_review`. It is not a readiness input and changes no gate.

The review was performed after the frozen `author_ready` artifacts were created.
Those artifacts correctly describe independent review as not yet run at freeze
time; they do not describe the later review recorded here.

## Reviewed State

- Public controller: `28ff9421a56a46a8333f7887ab692488d05d8da5`.
- Public author readiness: `2442911054473e9b03f90f9e4649a4c66b66fcdb`.
- Public status descendant: `64f29d25db44cb49b348fe8fd0898738fbc106e7`.
- Private source: `bc98e9ff0de6d525b8415a98040d341886c12591`.
- Private final: `c8bf86b9e28b9c8ea12f32988e195f2e084ae0ec`.
- Readiness SHA-256: `c280eb522ce31145d8572fee8235f305e2777fb8e47ebc4f94c2a2d287f17d75`.

## Executed Verification

The reviewer reported the following completed tool results, not just proposed
commands:

- Public session `53520`: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest
  discover -s evals/deliver/plain-language-v12/tests -p 'test_*.py'` exited 0;
  `Ran 72 tests in 435.108s`, `OK`.
- Private session `37741`: the committed author validator against the exact
  source/final above with `--require-public` exited 0. Its sanitized result
  reconciled 225 named controls: 28 positive and 197 negative, with no mismatch.
- The reviewer independently reconciled 108 unique cases, 103 retained
  behaviors, five approved removals, and 540 field obligations.
- All eight carried bundle files matched independent commit
  `ab2ce57b733c3f04629121cdf3e6dce845431240` by bytes and Git mode.
- Three distinct judge allocations remained `allocated_not_run`, using
  `gpt-5.6-sol` and `xhigh`.

## Source Inspection

The reviewer inspected startup ordering, exact Git-object staging, complete
runtime closure, clean exact private-final enforcement, delayed local imports,
import-path interference checks, pre/post drift, packet derivation and blinding,
aggregation, and the earlier invalid-version defect boundaries.

For the v12.34 repair it confirmed `python -I -B`, command-identity validation
of both flags, the sequential outer-sandbox then real-preflight regression,
and no remaining positional `command[3]` operation lookup in the inspected
public/private fixtures. It reported no material finding.

## Current Boundary

No actual root isolation, initialization, official arm, packet, or judge ran.
The attempted formal record write was rejected by auto-review before any write.
Both repositories remain unchanged. This note preserves the completed review
evidence while the formal transition remains blocked.

The user explicitly approved creating that transition record and continuing
the evaluation on 2026-09-15. That approval does not authorize invented results
or changes to frozen tests, scoring, or failure policy.
