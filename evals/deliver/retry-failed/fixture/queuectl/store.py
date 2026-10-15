"""Loading, validation, and atomic storage for queue state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


VALID_STATUSES = {"queued", "running", "failed", "done"}


class StateError(ValueError):
    """Raised when queue state is not valid."""


def load_state(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StateError(f"invalid JSON: {exc.msg}") from exc

    validate_state(state)
    return state


def validate_state(state: object) -> None:
    if not isinstance(state, dict):
        raise StateError("state must be a JSON object")
    if state.get("version") != 1:
        raise StateError("state version must be 1")

    jobs = state.get("jobs")
    if not isinstance(jobs, list):
        raise StateError("jobs must be a list")

    seen_ids: set[str] = set()
    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            raise StateError(f"jobs[{index}] must be an object")

        job_id = job.get("id")
        if not isinstance(job_id, str) or not job_id:
            raise StateError(f"jobs[{index}].id must be a non-empty string")
        if job_id in seen_ids:
            raise StateError(f"duplicate job id: {job_id}")
        seen_ids.add(job_id)

        if job.get("status") not in VALID_STATUSES:
            raise StateError(f"jobs[{index}].status is invalid")

        attempts = job.get("attempts")
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
            raise StateError(f"jobs[{index}].attempts must be a non-negative integer")

        failed_at = job.get("failed_at")
        if failed_at is not None and not isinstance(failed_at, str):
            raise StateError(f"jobs[{index}].failed_at must be a string")

        history = job.get("history")
        if history is not None and not isinstance(history, list):
            raise StateError(f"jobs[{index}].history must be a list")


def save_state_atomic(path: Path, state: dict[str, Any]) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(state, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
