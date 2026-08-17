# Acceptance Contract

The implementation is accepted when:

1. The existing public test suite passes.
2. The new command implements every behavior in `source-bullets.md` through the public CLI entry point.
3. Dry runs, invalid input, malformed state, and zero-selection runs leave the original state-file bytes unchanged.
4. Machine-readable output contains one parseable JSON object on stdout and no diagnostics on stdout.
5. Real retries preserve source ordering and unknown data while changing only the selected jobs' required fields.
6. Focused tests cover selection order, attempt limits, dry-run immutability, JSON output, malformed input, and compatibility with the existing commands.
7. The repository remains dependency-free and validates with `python3 -m unittest discover -s tests -v`.

The evaluation stops after local implementation, validation, and review. It must not push, open a pull request, merge, or modify the fixture's source repository.
