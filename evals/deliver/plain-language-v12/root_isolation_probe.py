#!/usr/bin/env python3
"""Host-dependent isolation probes for Deliver oracle v12.32.

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
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.32"
SCHEMA_VERSION = 1
HEX64 = re.compile(r"^[0-9a-f]{64}$")
OUTER_PROBE_ID = "deliver-v12.32-outer-sandbox-v1"
PREFLIGHT_PROBE_ID = "deliver-v12.32-real-preflight-v1"
TRANSITION_RELATIVE_PATH = "evals/deliver/plain-language-v12/readiness_transition.py"
PROBE_RELATIVE_PATH = "evals/deliver/plain-language-v12/root_isolation_probe.py"
HARNESS_RELATIVE_PATH = "evals/deliver/harness.py"
CASE_BUNDLE_VALIDATOR_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/case_bundle_validator.py"
)
BUNDLE_INTERFACE_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/independent-case-bundle-interface.json"
)
STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/standalone_case_bundle_validator.mjs"
)
DEPENDENCY_MANIFEST_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/root-isolation-dependencies.json"
)
DEPENDENCY_ROLES = {
    TRANSITION_RELATIVE_PATH: "readiness_transition_entrypoint",
    PROBE_RELATIVE_PATH: "root_isolation_probe_entrypoint",
    HARNESS_RELATIVE_PATH: "dynamic_deliver_harness_import",
    CASE_BUNDLE_VALIDATOR_RELATIVE_PATH: "private_bundle_integrity_validator",
    STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH: "standalone_bundle_validator_executable",
    BUNDLE_INTERFACE_RELATIVE_PATH: "independent_bundle_interface_data",
    "evals/deliver/plain-language-v12/adapter.py": "public_adapter_binding_data",
    "evals/deliver/plain-language-v12/baseline-package-manifest.json": "baseline_package_binding_data",
    "evals/deliver/plain-language-v12/candidate-behavior-map.json": "candidate_behavior_binding_data",
    "evals/deliver/plain-language-v12/candidate-package-manifest.json": "candidate_package_binding_data",
    "evals/deliver/plain-language-v12/comprehension-vocabulary.json": "response_schema_binding_data",
    "evals/deliver/plain-language-v12/execution-policy.json": "execution_policy_binding_data",
    "evals/deliver/plain-language-v12/public-contract-inventory.json": "public_inventory_binding_data",
    "evals/deliver/plain-language-v12/wording-approval.json": "wording_approval_binding_data",
}
PYTHON_SOURCE_DEPENDENCIES = frozenset({
    TRANSITION_RELATIVE_PATH,
    PROBE_RELATIVE_PATH,
    HARNESS_RELATIVE_PATH,
    CASE_BUNDLE_VALIDATOR_RELATIVE_PATH,
})
REPO_LOCAL_DATA_INPUTS = tuple(sorted(
    set(DEPENDENCY_ROLES) - PYTHON_SOURCE_DEPENDENCIES
    - {STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH}
))
CLOSURE_POLICY = {
    "normal_imports": "stdlib_only_ast_validated",
    "dynamic_imports": {
        PROBE_RELATIVE_PATH: [HARNESS_RELATIVE_PATH],
        TRANSITION_RELATIVE_PATH: [CASE_BUNDLE_VALIDATOR_RELATIVE_PATH],
    },
    "repo_local_subprocess_entrypoints": [STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH],
    "repo_local_data_inputs": list(REPO_LOCAL_DATA_INPUTS),
    "unlisted_repo_local_resolution_allowed": False,
    "execution_source": "verified_git_blobs_in_sealed_staging",
    "python_isolated_mode_required": True,
    "caller_pythonpath_allowed": False,
}
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


def _canonical_file_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(document, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _file_mode(path: Path) -> str:
    return "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644"


def _require_regular(root: Path, relative_path: str) -> Path:
    current = root
    for part in Path(relative_path).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise ProbeError(f"sealed dependency is unavailable: {relative_path}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ProbeError("sealed dependency closure contains a symlink")
    if not stat.S_ISREG(current.stat().st_mode):
        raise ProbeError("sealed dependency must be a regular file")
    return current


def _validate_staged_closure(closure_root: Path, expected_manifest_sha256: str) -> str:
    if closure_root.is_symlink():
        raise ProbeError("sealed dependency closure root cannot be a symlink")
    closure_root = closure_root.resolve(strict=True)
    if not closure_root.is_dir() or not HEX64.fullmatch(expected_manifest_sha256):
        raise ProbeError("sealed dependency closure arguments are invalid")
    manifest_path = _require_regular(closure_root, DEPENDENCY_MANIFEST_RELATIVE_PATH)
    raw = manifest_path.read_bytes()
    if sha256_bytes(raw) != expected_manifest_sha256:
        raise ProbeError("sealed dependency manifest digest drifted")
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("sealed dependency manifest is invalid JSON") from exc
    expected_fields = {
        "schema_version", "oracle_version", "manifest_kind", "entry_count", "entries",
        "entries_sha256", "closure_policy", "manifest_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_fields:
        raise ProbeError("sealed dependency manifest schema is not exact")
    entries = manifest.get("entries")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (
        manifest.get("schema_version") != 1
        or manifest.get("oracle_version") != ORACLE_VERSION
        or manifest.get("manifest_kind")
        != "root_isolation_repo_local_execution_and_data_dependency_closure"
        or not isinstance(entries, list)
        or manifest.get("entry_count") != len(entries)
        or manifest.get("entries_sha256") != sha256_bytes(canonical_json(entries))
        or manifest.get("closure_policy") != CLOSURE_POLICY
        or manifest.get("manifest_sha256") != sha256_bytes(canonical_json(payload))
        or raw != _canonical_file_bytes(manifest)
    ):
        raise ProbeError("sealed dependency manifest values are invalid")
    expected_paths = sorted(DEPENDENCY_ROLES)
    if [entry.get("path") for entry in entries if isinstance(entry, dict)] != expected_paths:
        raise ProbeError("sealed dependency manifest has missing or extra entries")
    observations: list[dict[str, str]] = []
    for entry in entries:
        path = _require_regular(closure_root, entry["path"])
        observed = {
            "path": entry["path"], "role": entry.get("role"),
            "sha256": sha256_bytes(path.read_bytes()), "git_mode": _file_mode(path),
        }
        expected = {
            "path": entry["path"], "role": DEPENDENCY_ROLES[entry["path"]],
            "sha256": entry.get("sha256"), "git_mode": entry.get("git_mode"),
        }
        if set(entry) != {"path", "role", "sha256", "git_mode"} or observed != expected:
            raise ProbeError("sealed dependency file bytes, mode, or role drifted")
        observations.append(observed)
    manifest_observation = {
        "path": DEPENDENCY_MANIFEST_RELATIVE_PATH,
        "role": "dependency_manifest_root",
        "sha256": sha256_bytes(raw),
        "git_mode": _file_mode(manifest_path),
    }
    observations.append(manifest_observation)
    observations.sort(key=lambda item: item["path"])
    observed_paths = sorted(
        path.relative_to(closure_root).as_posix()
        for path in closure_root.rglob("*") if path.is_file() or path.is_symlink()
    )
    if observed_paths != sorted((*DEPENDENCY_ROLES, DEPENDENCY_MANIFEST_RELATIVE_PATH)):
        raise ProbeError("sealed dependency staging file set is not exact")
    if sys.flags.isolated != 1 or "PYTHONPATH" in os.environ or "PYTHONHOME" in os.environ:
        raise ProbeError("probe Python process is not isolated from module shadowing")
    return sha256_bytes(canonical_json(observations))


def _load_harness(closure_root: Path) -> Any:
    path = closure_root / HARNESS_RELATIVE_PATH
    if path.is_symlink() or not path.is_file():
        raise ProbeError("frozen Deliver harness is unavailable")
    spec = importlib.util.spec_from_file_location("deliver_v1232_host_harness", path)
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


def _outer_sandbox(
    repo: Path, private_repo: Path, closure_root: Path, challenge: str,
    dependency_manifest_sha256: str, staged_observations_sha256: str,
) -> dict[str, Any]:
    harness = _load_harness(closure_root)
    evaluator_target = private_repo / "private-oracle/cases.json"
    if evaluator_target.is_symlink() or not evaluator_target.is_file():
        raise ProbeError("private evaluator sentinel is unavailable")
    evaluator_before = sha256_bytes(evaluator_target.read_bytes())
    created: list[Path] = []
    payload = ("deliver-v12.32-root-probe-" + challenge + "\n").encode("ascii")
    with tempfile.TemporaryDirectory(
        prefix="deliver-v1232-isolation-", dir="/private/tmp"
    ) as root_text, tempfile.TemporaryDirectory(
        prefix="deliver-v1232-other-temp-", dir="/private/tmp"
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
        home_target = Path(f"/Users/fromdarkness/.deliver-v1232-home-{challenge[:16]}")
        volume_target = Path(f"/Volumes/Code/.deliver-v1232-volume-{challenge[:16]}")
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
claims["stage_read_allowed"] = stage.read_bytes().startswith(b"deliver-v12.32-root-probe-")
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
                "dependency_manifest_sha256": dependency_manifest_sha256,
                "staged_dependency_observations_sha256": staged_observations_sha256,
            }
        finally:
            for path in created:
                if path.is_file() and not path.is_symlink():
                    path.unlink()


def _real_preflight(
    repo: Path, closure_root: Path, challenge: str, dependency_manifest_sha256: str,
    staged_observations_sha256: str,
) -> dict[str, Any]:
    harness = _load_harness(closure_root)
    with tempfile.TemporaryDirectory(
        prefix="deliver-v1232-preflight-evidence-", dir="/private/tmp"
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
            "dependency_manifest_sha256": dependency_manifest_sha256,
            "staged_dependency_observations_sha256": staged_observations_sha256,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("outer-sandbox", "real-preflight"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--closure-root", type=Path, required=True)
    parser.add_argument("--dependency-manifest-sha256", required=True)
    parser.add_argument("--private-repo", type=Path, required=True)
    parser.add_argument("--challenge", required=True)
    args = parser.parse_args()
    if not HEX64.fullmatch(args.challenge):
        raise ProbeError("probe challenge is malformed")
    repo = args.repo.resolve(strict=True)
    private_repo = args.private_repo.resolve(strict=True)
    staged_observations_sha256 = _validate_staged_closure(
        args.closure_root, args.dependency_manifest_sha256,
    )
    closure_root = args.closure_root.resolve(strict=True)
    result = (
        _outer_sandbox(
            repo, private_repo, closure_root, args.challenge,
            args.dependency_manifest_sha256, staged_observations_sha256,
        )
        if args.operation == "outer-sandbox"
        else _real_preflight(
            repo, closure_root, args.challenge,
            args.dependency_manifest_sha256, staged_observations_sha256,
        )
    )
    print(canonical_json(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProbeError as exc:
        print(f"root isolation probe failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
