"""Command-line interface for Queuectl."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from queuectl.store import StateError, load_state, save_state_atomic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="queuectl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list jobs")
    list_parser.add_argument("state", type=Path)

    failed_parser = subparsers.add_parser("mark-failed", help="mark a job failed")
    failed_parser.add_argument("state", type=Path)
    failed_parser.add_argument("job_id")
    failed_parser.add_argument("--at", required=True, dest="failed_at")

    return parser


def _read_state(path: Path) -> dict | None:
    try:
        return load_state(path)
    except (OSError, StateError) as exc:
        print(f"queuectl: {exc}", file=sys.stderr)
        return None


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state = _read_state(args.state)
    if state is None:
        return 2

    if args.command == "list":
        for job in state["jobs"]:
            print(f"{job['id']}\t{job['status']}\t{job['attempts']}")
        return 0

    if args.command == "mark-failed":
        for job in state["jobs"]:
            if job["id"] == args.job_id:
                job["status"] = "failed"
                job["failed_at"] = args.failed_at
                try:
                    save_state_atomic(args.state, state)
                except OSError as exc:
                    print(f"queuectl: {exc}", file=sys.stderr)
                    return 2
                return 0
        print(f"queuectl: unknown job id: {args.job_id}", file=sys.stderr)
        return 2

    raise AssertionError(f"unhandled command: {args.command}")


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
