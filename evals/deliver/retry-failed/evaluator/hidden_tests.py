from __future__ import annotations

import importlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


if len(sys.argv) < 2:
    raise SystemExit("usage: hidden_tests.py ARM_REPO")

ARM_REPO = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(ARM_REPO))
cli = importlib.import_module("queuectl.cli")


class RetryFailedAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.state_path = Path(self.temporary_directory.name) / "state.json"

    def write_state(self, state: object) -> bytes:
        original = (json.dumps(state, separators=(",", ":")) + "\n").encode()
        self.state_path.write_bytes(original)
        return original

    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                result = cli.main(list(arguments))
            except SystemExit as exc:
                result = int(exc.code)
        return result, stdout.getvalue(), stderr.getvalue()

    def complex_state(self) -> dict:
        return {
            "version": 1,
            "queue_name": "nightly",
            "jobs": [
                {
                    "id": "alpha",
                    "status": "failed",
                    "attempts": 1,
                    "failed_at": "2026-08-16T02:00:00Z",
                    "history": [{"action": "failed"}],
                    "owner": "ops",
                },
                {
                    "id": "beta",
                    "status": "failed",
                    "attempts": 0,
                    "failed_at": "2026-08-16T01:00:00Z",
                    "payload": {"kind": "email"},
                },
                {
                    "id": "gamma",
                    "status": "failed",
                    "attempts": 2,
                    "tag": "missing-time",
                },
                {
                    "id": "capped",
                    "status": "failed",
                    "attempts": 3,
                    "failed_at": "2026-08-15T01:00:00Z",
                },
                {"id": "queued", "status": "queued", "attempts": 0},
            ],
        }

    def test_real_retry_orders_limits_and_preserves_data(self) -> None:
        self.write_state(self.complex_state())

        result, stdout, stderr = self.run_cli(
            "retry-failed",
            str(self.state_path),
            "--limit",
            "2",
            "--max-attempts",
            "3",
            "--json",
        )

        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout),
            {"count": 2, "dry_run": False, "job_ids": ["beta", "alpha"]},
        )
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["queue_name"], "nightly")
        self.assertEqual([job["id"] for job in state["jobs"]], ["alpha", "beta", "gamma", "capped", "queued"])

        alpha, beta, gamma, capped, queued = state["jobs"]
        self.assertEqual(alpha["owner"], "ops")
        self.assertEqual(alpha["status"], "queued")
        self.assertEqual(alpha["attempts"], 2)
        self.assertNotIn("failed_at", alpha)
        self.assertEqual(alpha["history"], [{"action": "failed"}, {"action": "retried", "attempt": 2}])

        self.assertEqual(beta["payload"], {"kind": "email"})
        self.assertEqual(beta["status"], "queued")
        self.assertEqual(beta["attempts"], 1)
        self.assertNotIn("failed_at", beta)
        self.assertEqual(beta["history"], [{"action": "retried", "attempt": 1}])

        self.assertEqual(gamma, self.complex_state()["jobs"][2])
        self.assertEqual(capped, self.complex_state()["jobs"][3])
        self.assertEqual(queued, self.complex_state()["jobs"][4])

    def test_dry_run_uses_same_order_and_preserves_exact_bytes(self) -> None:
        original = self.write_state(self.complex_state())

        result, stdout, stderr = self.run_cli(
            "retry-failed",
            str(self.state_path),
            "--limit",
            "3",
            "--dry-run",
            "--json",
        )

        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout),
            {"count": 3, "dry_run": True, "job_ids": ["beta", "alpha", "gamma"]},
        )
        self.assertEqual(self.state_path.read_bytes(), original)

    def test_equal_timestamps_break_ties_by_id(self) -> None:
        self.write_state(
            {
                "version": 1,
                "jobs": [
                    {"id": "zulu", "status": "failed", "attempts": 0, "failed_at": "2026-08-16T01:00:00Z"},
                    {"id": "alpha", "status": "failed", "attempts": 0, "failed_at": "2026-08-16T01:00:00Z"},
                    {"id": "missing-b", "status": "failed", "attempts": 0},
                    {"id": "missing-a", "status": "failed", "attempts": 0},
                ],
            }
        )

        result, stdout, stderr = self.run_cli(
            "retry-failed", str(self.state_path), "--dry-run", "--json"
        )

        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout)["job_ids"],
            ["alpha", "zulu", "missing-a", "missing-b"],
        )

    def test_zero_selection_does_not_rewrite_file(self) -> None:
        original = self.write_state(
            {
                "version": 1,
                "jobs": [
                    {"id": "done", "status": "done", "attempts": 1},
                    {"id": "capped", "status": "failed", "attempts": 3},
                ],
            }
        )

        result, stdout, stderr = self.run_cli(
            "retry-failed", str(self.state_path), "--json"
        )

        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout),
            {"count": 0, "dry_run": False, "job_ids": []},
        )
        self.assertEqual(self.state_path.read_bytes(), original)

    def test_malformed_state_is_diagnostic_and_unchanged(self) -> None:
        original = self.write_state(
            {
                "version": 1,
                "jobs": [
                    {"id": "same", "status": "failed", "attempts": 0},
                    {"id": "same", "status": "failed", "attempts": 0},
                ],
            }
        )

        result, stdout, stderr = self.run_cli(
            "retry-failed", str(self.state_path), "--json"
        )

        self.assertEqual(result, 2)
        self.assertEqual(stdout, "")
        self.assertIn("duplicate job id", stderr)
        self.assertEqual(self.state_path.read_bytes(), original)

    def test_invalid_positive_integer_is_rejected_without_writing(self) -> None:
        original = self.write_state(self.complex_state())

        result, stdout, stderr = self.run_cli(
            "retry-failed", str(self.state_path), "--limit", "0", "--json"
        )

        self.assertEqual(result, 2)
        self.assertEqual(stdout, "")
        self.assertIn("positive", stderr.lower())
        self.assertEqual(self.state_path.read_bytes(), original)

    def test_human_output_names_jobs_and_dry_run(self) -> None:
        self.write_state(self.complex_state())

        result, stdout, stderr = self.run_cli(
            "retry-failed", str(self.state_path), "--limit", "1", "--dry-run"
        )

        self.assertEqual(result, 0)
        self.assertEqual(stderr, "")
        self.assertIn("beta", stdout)
        self.assertIn("dry", stdout.lower())


if __name__ == "__main__":
    unittest.main()
