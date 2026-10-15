# Add `retry-failed` to Queuectl

- Add `queuectl retry-failed STATE` with optional `--limit N`, `--max-attempts N`, `--dry-run`, and `--json` flags.
- `--limit` and `--max-attempts` must be positive integers. `--max-attempts` defaults to `3`. With no `--limit`, retry every eligible job.
- A job is eligible when its status is `failed` and its integer `attempts` value is less than `--max-attempts`.
- Select eligible jobs by oldest `failed_at` first, break equal timestamps by job ID, and place jobs with no `failed_at` after timestamped failures, again ordered by job ID.
- A real retry changes each selected job to `queued`, increments `attempts`, removes `failed_at`, and appends `{"action": "retried", "attempt": NEW_ATTEMPT}` to its existing `history` list. Create the list when it is absent.
- Preserve the order of jobs, all unknown top-level fields, all unknown job fields, and every unselected job exactly as data.
- `--dry-run` must select and report the same jobs without changing the state file in any way.
- `--json` must print exactly one JSON object to stdout with `count`, `dry_run`, and ordered `job_ids` fields. Human output should also identify the selected jobs and whether the run was a dry run.
- Invalid flags, unreadable JSON, or malformed state must exit with status `2`, write a useful diagnostic to stderr, and leave the state file unchanged.
- Do not rewrite the state file when no jobs are eligible.
- Keep the existing `list` and `mark-failed` behavior working. Add focused tests and update the README.
