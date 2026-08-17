from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from queuectl.cli import main


class QueuectlCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_path = Path(self.temporary_directory.name) / "state.json"
        self.write_state(
            {
                "version": 1,
                "jobs": [
                    {"id": "alpha", "status": "queued", "attempts": 0},
                    {"id": "beta", "status": "done", "attempts": 1},
                ],
            }
        )

    def write_state(self, state: object) -> None:
        self.state_path.write_text(json.dumps(state), encoding="utf-8")

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(list(arguments))
        return result, stdout.getvalue(), stderr.getvalue()

    def test_list_prints_jobs_in_state_order(self) -> None:
        result, stdout, stderr = self.run_cli("list", str(self.state_path))

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "alpha\tqueued\t0\nbeta\tdone\t1\n")
        self.assertEqual(stderr, "")

    def test_mark_failed_updates_only_selected_job(self) -> None:
        result, stdout, stderr = self.run_cli(
            "mark-failed",
            str(self.state_path),
            "alpha",
            "--at",
            "2026-08-16T12:00:00Z",
        )

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            state["jobs"],
            [
                {
                    "id": "alpha",
                    "status": "failed",
                    "attempts": 0,
                    "failed_at": "2026-08-16T12:00:00Z",
                },
                {"id": "beta", "status": "done", "attempts": 1},
            ],
        )

    def test_invalid_json_returns_two_without_writing(self) -> None:
        original = b"{broken"
        self.state_path.write_bytes(original)

        result, stdout, stderr = self.run_cli("list", str(self.state_path))

        self.assertEqual(result, 2)
        self.assertEqual(stdout, "")
        self.assertIn("invalid JSON", stderr)
        self.assertEqual(self.state_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
