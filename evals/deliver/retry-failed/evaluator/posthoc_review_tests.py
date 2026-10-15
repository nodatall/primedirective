from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


if len(sys.argv) < 2:
    raise SystemExit("usage: posthoc_review_tests.py ARM_REPO")

ARM_REPO = Path(sys.argv.pop(1)).resolve()


class PostReviewRegressionTests(unittest.TestCase):
    def run_retry(self, source: bytes, *options: str) -> tuple[subprocess.CompletedProcess[bytes], bytes]:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state_path.write_bytes(source)
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "queuectl.cli",
                    "retry-failed",
                    str(state_path),
                    *options,
                ],
                cwd=ARM_REPO,
                env=environment,
                capture_output=True,
                check=False,
            )
            return result, state_path.read_bytes()

    def encoded(self, state: object) -> bytes:
        return (json.dumps(state, separators=(",", ":")) + "\n").encode()

    def one_failed_job(self, **overrides: object) -> dict:
        job = {
            "id": "job",
            "status": "failed",
            "attempts": 1,
            "failed_at": "2026-01-01T00:00:00Z",
        }
        job.update(overrides)
        return {"version": 1, "jobs": [job]}

    def assert_rejected_unchanged(
        self, source: bytes, *options: str
    ) -> subprocess.CompletedProcess[bytes]:
        result, after = self.run_retry(source, *options)
        self.assertEqual(result.returncode, 2, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertEqual(after, source)
        return result

    def test_null_history_is_treated_as_absent(self) -> None:
        source = self.encoded(self.one_failed_job(history=None))
        result, after = self.run_retry(source, "--json")

        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        history = json.loads(after)["jobs"][0]["history"]
        self.assertEqual(history, [{"action": "retried", "attempt": 2}])

    def test_container_status_is_rejected(self) -> None:
        source = self.encoded(self.one_failed_job(status=[]))
        self.assert_rejected_unchanged(source, "--json")

    def test_invalid_utf8_is_rejected(self) -> None:
        self.assert_rejected_unchanged(b"\xff\xfe{not-json", "--json")

    def test_boolean_version_is_rejected(self) -> None:
        state = self.one_failed_job()
        state["version"] = True
        source = self.encoded(state)
        self.assert_rejected_unchanged(source, "--json")

    def test_mixed_offsets_are_ordered_by_instant(self) -> None:
        source = self.encoded(
            {
                "version": 1,
                "jobs": [
                    {
                        "id": "later",
                        "status": "failed",
                        "attempts": 0,
                        "failed_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": "earlier",
                        "status": "failed",
                        "attempts": 0,
                        "failed_at": "2026-01-01T00:30:00+01:00",
                    },
                ],
            }
        )
        result, after = self.run_retry(source, "--limit", "1", "--dry-run", "--json")

        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(json.loads(result.stdout)["job_ids"], ["earlier"])
        self.assertEqual(after, source)

    def test_lone_surrogate_id_cannot_fail_after_persistence(self) -> None:
        source = self.encoded(self.one_failed_job(id="\ud800"))
        result, after = self.run_retry(source)

        self.assertEqual(result.returncode, 2, result.stderr.decode(errors="replace"))
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertEqual(after, source)

    def test_json_decoder_integer_limit_is_normalized(self) -> None:
        source = (
            b'{"version":1,"unknown":'
            + (b"9" * 5000)
            + b',"jobs":[{"id":"job","status":"failed","attempts":0}]}'
        )
        self.assert_rejected_unchanged(source, "--json")

    def test_nonfinite_json_constant_is_rejected(self) -> None:
        source = b'{"version":1,"unknown":NaN,"jobs":[{"id":"job","status":"failed","attempts":0}]}'
        self.assert_rejected_unchanged(source, "--json")

    def test_overflowing_unknown_number_is_not_rewritten_as_infinity(self) -> None:
        source = b'{"version":1,"unknown":1e400,"jobs":[{"id":"job","status":"failed","attempts":0}]}'
        self.assert_rejected_unchanged(source, "--json")

    def test_submicrosecond_ordering_does_not_select_later_job(self) -> None:
        source = self.encoded(
            {
                "version": 1,
                "jobs": [
                    {
                        "id": "z-earlier",
                        "status": "failed",
                        "attempts": 0,
                        "failed_at": "2026-01-01T00:00:00.0000001Z",
                    },
                    {
                        "id": "a-later",
                        "status": "failed",
                        "attempts": 0,
                        "failed_at": "2026-01-01T00:00:00.0000002Z",
                    },
                ],
            }
        )
        result, after = self.run_retry(source, "--limit", "1", "--dry-run", "--json")

        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(json.loads(result.stdout)["job_ids"], ["z-earlier"])
        self.assertEqual(after, source)

    def test_human_output_does_not_emit_job_id_controls(self) -> None:
        source = self.encoded(self.one_failed_job(id="job\nqueuectl: forged\u001b[2J"))
        result, after = self.run_retry(source, "--dry-run")

        if result.returncode == 0:
            self.assertNotIn(b"\x1b", result.stdout)
            self.assertEqual(result.stdout.count(b"\n"), 1)
            self.assertEqual(after, source)
        else:
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"Traceback", result.stderr)
            self.assertEqual(after, source)


if __name__ == "__main__":
    unittest.main()
