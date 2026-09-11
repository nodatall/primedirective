#!/usr/bin/env python3
"""Launch the frozen private comparison runtime without importing checkout code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.34"
READINESS_RELATIVE_PATH = "evals/deliver/plain-language-v12/oracle-readiness.json"
CLOSURE_MANIFEST_RELATIVE_PATH = "private-oracle/private-runtime-closure.json"
RUNTIME_ENTRYPOINT = "private-oracle/comparison_runtime.py"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_RUNTIME_ROLES = {
    "private-oracle/cases.json": "hidden_case_data",
    RUNTIME_ENTRYPOINT: "comparison_runtime_entrypoint",
    "private-oracle/deterministic_scorer.py": "deterministic_scorer_import",
    "private-oracle/expected-answers.json": "hidden_expected_answer_data",
    "private-oracle/identity-denylist.txt": "judge_identity_policy_data",
    "private-oracle/response-schema.json": "typed_response_schema_data",
}
LAUNCH_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "LANG": "en_US.UTF-8",
    "LC_ALL": "en_US.UTF-8",
    "PYTHONSAFEPATH": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}


class PrivateRuntimeLaunchError(RuntimeError):
    """Raised when the private runtime cannot be launched from frozen Git objects."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git(repo: Path, arguments: list[str], *, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["/usr/bin/git", *arguments], cwd=repo, check=False,
        capture_output=True, text=not binary,
    )
    if result.returncode:
        stderr = result.stderr.decode(errors="replace") if binary else result.stderr
        raise PrivateRuntimeLaunchError(
            f"git {' '.join(arguments)} failed: {stderr.strip()}"
        )
    return result.stdout if binary else result.stdout.strip()


def _commit(repo: Path, ref: str) -> str:
    value = str(_git(repo, ["rev-parse", f"{ref}^{{commit}}"])).strip()
    if HEX40.fullmatch(value) is None:
        raise PrivateRuntimeLaunchError("private final commit is malformed")
    return value


def _blob(repo: Path, commit: str, relative_path: str) -> bytes:
    return bytes(_git(repo, ["cat-file", "blob", f"{commit}:{relative_path}"], binary=True))


def _tree_entry(repo: Path, commit: str, relative_path: str) -> tuple[str, str]:
    lines = str(_git(repo, ["ls-tree", commit, "--", relative_path])).splitlines()
    if len(lines) != 1:
        raise PrivateRuntimeLaunchError(f"private closure entry is missing: {relative_path}")
    try:
        metadata, listed = lines[0].split("\t", 1)
        mode, kind, object_id = metadata.split()
    except ValueError as exc:
        raise PrivateRuntimeLaunchError("private closure Git metadata is malformed") from exc
    if (
        listed != relative_path
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or HEX40.fullmatch(object_id) is None
    ):
        raise PrivateRuntimeLaunchError(
            f"private closure entry is not a regular Git blob: {relative_path}"
        )
    return mode, object_id


def _file_mode(path: Path) -> str:
    return "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644"


def _require_regular(root: Path, relative_path: str) -> Path:
    current = root
    for part in Path(relative_path).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise PrivateRuntimeLaunchError(
                f"private closure file is unavailable: {relative_path}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise PrivateRuntimeLaunchError(
                f"private closure contains a symlink: {relative_path}"
            )
    if not stat.S_ISREG(current.stat().st_mode):
        raise PrivateRuntimeLaunchError(
            f"private closure entry is not regular: {relative_path}"
        )
    return current


def _load_document(value: bytes, label: str) -> dict[str, Any]:
    try:
        document = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrivateRuntimeLaunchError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise PrivateRuntimeLaunchError(f"{label} must be an object")
    return document


def require_clean_exact_private_final(private_repo: Path, final_commit: str) -> Path:
    private_repo = private_repo.resolve(strict=True)
    if private_repo.is_symlink() or not (private_repo / ".git").exists():
        raise PrivateRuntimeLaunchError("private evaluator repository is unavailable")
    if _commit(private_repo, final_commit) != final_commit:
        raise PrivateRuntimeLaunchError("private final commit does not resolve exactly")
    if _commit(private_repo, "HEAD") != final_commit:
        raise PrivateRuntimeLaunchError("private evaluator HEAD is not the exact frozen final")
    status = str(_git(private_repo, ["status", "--porcelain=v1", "--untracked-files=all"]))
    if status.strip():
        raise PrivateRuntimeLaunchError(
            "private evaluator worktree is not completely clean, including untracked files"
        )
    return private_repo


def validate_manifest(
    private_repo: Path, final_commit: str, expected_sha256: str,
) -> tuple[dict[str, Any], bytes]:
    if HEX64.fullmatch(expected_sha256) is None:
        raise PrivateRuntimeLaunchError("private closure manifest digest is malformed")
    raw = _blob(private_repo, final_commit, CLOSURE_MANIFEST_RELATIVE_PATH)
    if sha256_bytes(raw) != expected_sha256:
        raise PrivateRuntimeLaunchError("private closure manifest digest drifted")
    manifest = _load_document(raw, "private runtime closure manifest")
    expected_fields = {
        "schema_version", "oracle_version", "manifest_kind", "entrypoint",
        "entry_count", "entries", "entries_sha256", "manifest_sha256",
    }
    entries = manifest.get("entries")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (
        set(manifest) != expected_fields
        or manifest.get("schema_version") != 1
        or manifest.get("oracle_version") != ORACLE_VERSION
        or manifest.get("manifest_kind") != "private_runtime_git_object_execution_closure"
        or manifest.get("entrypoint") != RUNTIME_ENTRYPOINT
        or not isinstance(entries, list)
        or manifest.get("entry_count") != len(entries)
        or manifest.get("entries_sha256") != sha256_bytes(canonical_json(entries))
        or manifest.get("manifest_sha256") != sha256_bytes(canonical_json(payload))
        or raw != json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    ):
        raise PrivateRuntimeLaunchError("private closure manifest schema is not exact")
    expected_entries = []
    for relative_path in sorted(PRIVATE_RUNTIME_ROLES):
        mode, object_id = _tree_entry(private_repo, final_commit, relative_path)
        expected_entries.append({
            "path": relative_path,
            "role": PRIVATE_RUNTIME_ROLES[relative_path],
            "sha256": sha256_bytes(_blob(private_repo, final_commit, relative_path)),
            "git_blob": object_id,
            "git_mode": mode,
        })
    if entries != expected_entries:
        raise PrivateRuntimeLaunchError(
            "private closure manifest has a missing, extra, mode, blob, or digest mismatch"
        )
    return manifest, raw


def stage_closure(
    private_repo: Path, final_commit: str, manifest: dict[str, Any],
    manifest_raw: bytes, destination: Path,
) -> list[dict[str, str]]:
    all_entries = [
        *manifest["entries"],
        {
            "path": CLOSURE_MANIFEST_RELATIVE_PATH,
            "role": "private_runtime_closure_manifest",
            "sha256": sha256_bytes(manifest_raw),
            "git_blob": _tree_entry(
                private_repo, final_commit, CLOSURE_MANIFEST_RELATIVE_PATH
            )[1],
            "git_mode": _tree_entry(
                private_repo, final_commit, CLOSURE_MANIFEST_RELATIVE_PATH
            )[0],
        },
    ]
    for entry in all_entries:
        target = destination / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            raise PrivateRuntimeLaunchError("private staging target already exists")
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(_blob(private_repo, final_commit, entry["path"]))
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        target.chmod(0o755 if entry["git_mode"] == "100755" else 0o644)
    return validate_staged_closure(destination, manifest, manifest_raw)


def validate_staged_closure(
    destination: Path, manifest: dict[str, Any], manifest_raw: bytes,
) -> list[dict[str, str]]:
    expected = {
        entry["path"]: entry
        for entry in manifest["entries"]
    }
    expected[CLOSURE_MANIFEST_RELATIVE_PATH] = {
        "path": CLOSURE_MANIFEST_RELATIVE_PATH,
        "role": "private_runtime_closure_manifest",
        "sha256": sha256_bytes(manifest_raw),
        "git_mode": "100644",
    }
    observed_paths = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*") if path.is_file() or path.is_symlink()
    )
    if observed_paths != sorted(expected):
        raise PrivateRuntimeLaunchError("private staged closure file set is not exact")
    observations: list[dict[str, str]] = []
    for relative_path in observed_paths:
        path = _require_regular(destination, relative_path)
        entry = expected[relative_path]
        observation = {
            "path": relative_path,
            "role": entry["role"],
            "sha256": sha256_bytes(path.read_bytes()),
            "git_mode": _file_mode(path),
        }
        if (
            observation["sha256"] != entry["sha256"]
            or observation["git_mode"] != entry["git_mode"]
        ):
            raise PrivateRuntimeLaunchError("private staged closure bytes or mode drifted")
        observations.append(observation)
    return observations


def _read_readiness(public_repo: Path) -> tuple[dict[str, Any], bytes]:
    readiness = _require_regular(public_repo, READINESS_RELATIVE_PATH).read_bytes()
    return _load_document(readiness, "public readiness"), readiness


def launch(
    public_repo: Path, private_repo: Path, runtime_arguments: list[str],
) -> subprocess.CompletedProcess[str]:
    public_repo = public_repo.resolve(strict=True)
    readiness, _ = _read_readiness(public_repo)
    final_commit = str(readiness.get("private_evaluator_commit"))
    manifest_sha256 = str(readiness.get("private_runtime_closure_manifest_sha256"))
    if (
        readiness.get("oracle_version") != ORACLE_VERSION
        or readiness.get("status") != "ready"
        or HEX40.fullmatch(final_commit) is None
        or HEX64.fullmatch(manifest_sha256) is None
        or readiness.get("private_runtime_closure_manifest_path")
        != CLOSURE_MANIFEST_RELATIVE_PATH
    ):
        raise PrivateRuntimeLaunchError("public readiness cannot authorize private runtime")
    private_repo = require_clean_exact_private_final(private_repo, final_commit)
    manifest, manifest_raw = validate_manifest(private_repo, final_commit, manifest_sha256)
    python = Path(sys.executable).resolve(strict=True)
    if not python.is_file() or not os.access(python, os.X_OK):
        raise PrivateRuntimeLaunchError("isolated Python executable is unavailable")
    with tempfile.TemporaryDirectory(
        prefix="deliver-v1234-private-runtime-", dir="/private/tmp"
    ) as temporary:
        stage = Path(temporary)
        observations = stage_closure(
            private_repo, final_commit, manifest, manifest_raw, stage,
        )
        environment = {
            **LAUNCH_ENVIRONMENT,
            "DELIVER_PRIVATE_ORIGIN_REPO": str(private_repo),
            "DELIVER_PRIVATE_FINAL_COMMIT": final_commit,
            "DELIVER_PRIVATE_RUNTIME_CLOSURE_SHA256": manifest_sha256,
            "DELIVER_PRIVATE_RUNTIME_STAGE": str(stage),
            "DELIVER_PRIVATE_RUNTIME_STAGE_OBSERVATIONS_SHA256": sha256_bytes(
                canonical_json(observations)
            ),
        }
        bootstrap = (
            "import runpy,sys;"
            f"sys.path[:0]=[{str((stage / 'private-oracle').resolve())!r}];"
            f"sys.argv=[{str((stage / RUNTIME_ENTRYPOINT).resolve())!r},*sys.argv[1:]];"
            "runpy.run_path(sys.argv[0],run_name='__main__')"
        )
        command = [str(python), "-I", "-B", "-c", bootstrap, *runtime_arguments]
        completed = subprocess.run(
            command, cwd=stage, env=environment, check=False,
            capture_output=True, text=True,
        )
        if validate_staged_closure(stage, manifest, manifest_raw) != observations:
            raise PrivateRuntimeLaunchError("private staged closure drifted during execution")
    require_clean_exact_private_final(private_repo, final_commit)
    return completed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-repo", type=Path, required=True)
    parser.add_argument("--private-repo", type=Path, required=True)
    parser.add_argument("runtime_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    runtime_arguments = list(args.runtime_arguments)
    if runtime_arguments[:1] == ["--"]:
        runtime_arguments.pop(0)
    if not runtime_arguments:
        raise PrivateRuntimeLaunchError("private runtime operation is required")
    completed = launch(args.public_repo, args.private_repo, runtime_arguments)
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, PrivateRuntimeLaunchError) as exc:
        print(f"private runtime launch failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
