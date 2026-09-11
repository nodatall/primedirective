#!/usr/bin/env python3
"""Host-dependent isolation probes for Deliver oracle v12.30.

This module is only invoked by the frozen ``run-root-isolation`` readiness
operation. It emits machine evidence; it never writes readiness state.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.30"
SCHEMA_VERSION = 1
HEX64 = re.compile(r"^[0-9a-f]{64}$")
OUTER_PROBE_ID = "deliver-v12.30-outer-sandbox-v1"
PREFLIGHT_PROBE_ID = "deliver-v12.30-real-preflight-v1"
OUTER_CLAIMS = (
    "stage_read_allowed",
    "stage_write_allowed",
    "sibling_read_denied",
    "sibling_write_denied",
    "evaluator_read_denied",
    "evaluator_write_denied",
    "other_temp_read_denied",
    "other_temp_write_denied",
    "home_read_denied",
    "home_write_denied",
    "volume_read_denied",
    "volume_write_denied",
    "external_sentinel_unchanged",
)
PREFLIGHT_CLAIMS = (
    "isolated_codex_home",
    "isolated_home",
    "isolated_tmpdir",
    "empty_inherited_environment",
    "credential_copy_boundary",
    "pinned_bundled_codex_identity",
    "required_codex_connectivity",
)


class ProbeError(RuntimeError):
    """Raised when a required host observation is unavailable or fails."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_harness(repo: Path) -> Any:
    path = repo / "evals/deliver/harness.py"
    if path.is_symlink() or not path.is_file():
        raise ProbeError("frozen Deliver harness is unavailable")
    spec = importlib.util.spec_from_file_location("deliver_v1230_host_harness", path)
    if spec is None or spec.loader is None:
        raise ProbeError("frozen Deliver harness cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _regular_sentinel(path: Path, payload: bytes) -> str:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return sha256_bytes(payload)


def _outer_sandbox(repo: Path, private_repo: Path, challenge: str) -> dict[str, Any]:
    harness = _load_harness(repo)
    evaluator_target = private_repo / "private-oracle/cases.json"
    if evaluator_target.is_symlink() or not evaluator_target.is_file():
        raise ProbeError("private evaluator sentinel is unavailable")
    evaluator_before = sha256_bytes(evaluator_target.read_bytes())
    created: list[Path] = []
    payload = ("deliver-v12.30-root-probe-" + challenge + "\n").encode("ascii")
    with tempfile.TemporaryDirectory(
        prefix="deliver-v1230-isolation-", dir="/private/tmp"
    ) as root_text, tempfile.TemporaryDirectory(
        prefix="deliver-v1230-other-temp-", dir="/private/tmp"
    ) as other_text:
        root = Path(root_text)
        other_root = Path(other_text)
        stage = root / "current-arm"
        stage_repo = stage / "repo"
        sibling = root / "runner-sibling-probe"
        stage_repo.mkdir(parents=True)
        sibling.mkdir()
        (stage_repo / "stage-input.txt").write_bytes(payload)
        sibling_target = sibling / "sentinel.txt"
        other_target = other_root / "sentinel.txt"
        _regular_sentinel(sibling_target, payload)
        other_digest = _regular_sentinel(other_target, payload)
        home_target = Path(f"/Users/fromdarkness/.deliver-v1230-home-{challenge[:16]}")
        volume_target = Path(f"/Volumes/Code/.deliver-v1230-volume-{challenge[:16]}")
        try:
            for target in (home_target, volume_target):
                _regular_sentinel(target, payload)
                created.append(target)
            profile = root / "outer-runner.sb"
            profile.write_text(harness.sandbox_profile(stage), encoding="utf-8")
            script = r'''from pathlib import Path
import json
import sys

stage, sibling, evaluator, other_temp, home, volume = map(Path, sys.argv[1:7])
claims = {}
claims["stage_read_allowed"] = stage.read_bytes().startswith(b"deliver-v12.30-root-probe-")
(stage.parent / "stage-output.txt").write_bytes(b"stage-write-ok\n")
claims["stage_write_allowed"] = (stage.parent / "stage-output.txt").read_bytes() == b"stage-write-ok\n"
for label, path in (
    ("sibling", sibling),
    ("evaluator", evaluator),
    ("other_temp", other_temp),
    ("home", home),
    ("volume", volume),
):
    try:
        path.read_bytes()
    except OSError:
        claims[label + "_read_denied"] = True
    else:
        claims[label + "_read_denied"] = False
    try:
        path.write_bytes(b"tamper\n")
    except OSError:
        claims[label + "_write_denied"] = True
    else:
        claims[label + "_write_denied"] = False
print(json.dumps(claims, sort_keys=True, separators=(",", ":")))
'''
            result = subprocess.run(
                [
                    str(harness.SANDBOX_EXEC), "-f", str(profile), sys.executable,
                    "-I", "-c", script,
                    str(stage_repo / "stage-input.txt"), str(sibling_target),
                    str(evaluator_target), str(other_target), str(home_target),
                    str(volume_target),
                ],
                cwd=stage_repo,
                env={
                    "PATH": "/usr/bin:/bin",
                    "LANG": "en_US.UTF-8",
                    "LC_ALL": "en_US.UTF-8",
                },
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 71 and "sandbox_apply: Operation not permitted" in result.stderr:
                raise ProbeError("outer sandbox probe was skipped by the enclosing host")
            if result.returncode != 0 or result.stderr:
                raise ProbeError("outer sandbox probe failed")
            try:
                observed = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise ProbeError("outer sandbox probe emitted invalid evidence") from exc
            expected_inner = set(OUTER_CLAIMS) - {"external_sentinel_unchanged"}
            if not isinstance(observed, dict) or set(observed) != expected_inner:
                raise ProbeError("outer sandbox probe evidence fields are incomplete")
            observed["external_sentinel_unchanged"] = (
                sha256_bytes(other_target.read_bytes()) == other_digest
                and sha256_bytes(evaluator_target.read_bytes()) == evaluator_before
                and all(sha256_bytes(path.read_bytes()) == sha256_bytes(payload) for path in created)
            )
            if any(observed.get(name) is not True for name in OUTER_CLAIMS):
                raise ProbeError("outer sandbox probe did not prove every required boundary")
            return {
                "schema_version": SCHEMA_VERSION,
                "oracle_version": ORACLE_VERSION,
                "probe_id": OUTER_PROBE_ID,
                "challenge": challenge,
                "result": "pass",
                "claims": observed,
                "sandbox_profile_sha256": sha256_bytes(profile.read_bytes()),
            }
        finally:
            for path in created:
                if path.is_file() and not path.is_symlink():
                    path.unlink()


def _real_preflight(repo: Path, challenge: str) -> dict[str, Any]:
    harness = _load_harness(repo)
    with tempfile.TemporaryDirectory(
        prefix="deliver-v1230-preflight-evidence-", dir="/private/tmp"
    ) as root_text:
        output = Path(root_text) / "runner-preflight.json"
        try:
            harness.preflight_runner(output)
        except harness.HarnessError as exc:
            if "sandbox_apply: Operation not permitted" in str(exc):
                raise ProbeError("real preflight was skipped by the enclosing host") from exc
            raise ProbeError("real bundled Codex preflight failed") from exc
        artifact = harness.validate_runner_preflight(output, check_binary=True)
        smoke = artifact["smoke"]
        environment = dict(item.split("=", 1) for item in smoke["environment"])
        command = smoke["command"]
        state_home = Path(environment["CODEX_HOME"])
        tmpdir = Path(environment["TMPDIR"])
        expected_keys = {
            "CODEX_HOME", "HOME", "TMPDIR", harness.EXTERNAL_SENTINEL_ENV,
            "PATH", "LANG", "LC_ALL", "TERM",
        }
        claims = {
            "isolated_codex_home": state_home.is_absolute()
                and str(state_home).startswith("/private/tmp/deliver-eval-preflight-"),
            "isolated_home": environment["HOME"] == environment["CODEX_HOME"],
            "isolated_tmpdir": tmpdir.is_absolute()
                and str(tmpdir).startswith("/private/tmp/deliver-eval-preflight-"),
            "empty_inherited_environment": set(environment) == expected_keys
                and "/usr/bin/env" in command and "-i" in command,
            "credential_copy_boundary": not (state_home / "auth.json").exists(),
            "pinned_bundled_codex_identity": artifact["binary_path"] == str(harness.BUNDLED_CODEX)
                and artifact["binary_sha256"] == harness.runner_identity()["sha256"],
            "required_codex_connectivity": smoke["exit_code"] == 0,
        }
        harness.validate_runner_trace(smoke["trace"].encode("utf-8"))
        if any(claims.get(name) is not True for name in PREFLIGHT_CLAIMS):
            raise ProbeError("real preflight did not prove every required boundary")
        return {
            "schema_version": SCHEMA_VERSION,
            "oracle_version": ORACLE_VERSION,
            "probe_id": PREFLIGHT_PROBE_ID,
            "challenge": challenge,
            "result": "pass",
            "claims": claims,
            "bundled_codex_identity": {
                "path": artifact["binary_path"],
                "version": artifact["binary_version"],
                "sha256": artifact["binary_sha256"],
            },
            "runner_trace_sha256": smoke["trace_sha256"],
            "runner_profile_sha256": smoke["profile_sha256"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("outer-sandbox", "real-preflight"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--private-repo", type=Path, required=True)
    parser.add_argument("--challenge", required=True)
    args = parser.parse_args()
    if not HEX64.fullmatch(args.challenge):
        raise ProbeError("probe challenge is malformed")
    repo = args.repo.resolve(strict=True)
    private_repo = args.private_repo.resolve(strict=True)
    result = (
        _outer_sandbox(repo, private_repo, args.challenge)
        if args.operation == "outer-sandbox"
        else _real_preflight(repo, args.challenge)
    )
    print(canonical_json(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProbeError as exc:
        print(f"root isolation probe failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
