# Queuectl

Queuectl is a dependency-free command-line tool for inspecting a small JSON job queue.

## State file

```json
{
  "version": 1,
  "jobs": [
    {
      "id": "email-weekly-report",
      "status": "queued",
      "attempts": 0
    }
  ]
}
```

Job IDs must be unique. Supported statuses are `queued`, `running`, `failed`, and `done`.

## Commands

List jobs:

```bash
python3 -m queuectl.cli list state.json
```

Mark a job as failed:

```bash
python3 -m queuectl.cli mark-failed state.json email-weekly-report --at 2026-08-16T12:00:00Z
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```
