from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "private_runtime_launcher.py"
SPEC = importlib.util.spec_from_file_location("deliver_v1233_private_runtime_launcher", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class PrivateRuntimeLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="deliver-v1233-launcher-", dir="/private/tmp"))
        self.addCleanup(shutil.rmtree, self.base)
        self.private = self.base / "private"
        self.public = self.base / "public"
        self.private.mkdir()
        self.public.mkdir()
        self._init(self.private)
        for relative, role in launcher.PRIVATE_RUNTIME_ROLES.items():
            path = self.private / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative == launcher.RUNTIME_ENTRYPOINT:
                path.write_text(
                    "import deterministic_scorer\n"
                    "import json, os, sys\n"
                    "assert sys.flags.isolated == 1\n"
                    "assert 'PYTHONPATH' not in os.environ\n"
                    "print(json.dumps({'source': deterministic_scorer.SOURCE}, sort_keys=True))\n",
                    encoding="utf-8",
                )
            elif relative.endswith("deterministic_scorer.py"):
                path.write_text("SOURCE = 'verified-git-blob'\n", encoding="utf-8")
            elif relative.endswith(".json"):
                path.write_text("{}\n", encoding="utf-8")
            else:
                path.write_text("identity-policy\n", encoding="utf-8")
            path.chmod(0o644)
        self._commit(self.private, "runtime source")
        self.source = self._git(self.private, "rev-parse", "HEAD")
        self._write_manifest()
        self._commit(self.private, "runtime closure")
        self.final = self._git(self.private, "rev-parse", "HEAD")
        self.manifest_sha256 = launcher.sha256_bytes(
            (self.private / launcher.CLOSURE_MANIFEST_RELATIVE_PATH).read_bytes()
        )
        readiness = {
            "oracle_version": launcher.ORACLE_VERSION,
            "status": "ready",
            "private_evaluator_commit": self.final,
            "private_runtime_closure_manifest_path": launcher.CLOSURE_MANIFEST_RELATIVE_PATH,
            "private_runtime_closure_manifest_sha256": self.manifest_sha256,
        }
        path = self.public / launcher.READINESS_RELATIVE_PATH
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(readiness), encoding="utf-8")

    def _git(self, repo: Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments], cwd=repo, check=True, capture_output=True, text=True,
        ).stdout.strip()

    def _init(self, repo: Path) -> None:
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.email", "launcher-test@example.invalid")
        self._git(repo, "config", "user.name", "Launcher Test")

    def _commit(self, repo: Path, message: str) -> None:
        self._git(repo, "add", ".")
        self._git(repo, "commit", "-q", "-m", message)

    def _write_manifest(self, mutate=None) -> None:
        entries = []
        ref = "HEAD"
        for relative, role in sorted(launcher.PRIVATE_RUNTIME_ROLES.items()):
            metadata = self._git(self.private, "ls-tree", ref, "--", relative).split("\t", 1)[0]
            mode, _kind, object_id = metadata.split()
            raw = subprocess.run(
                ["git", "cat-file", "blob", f"{ref}:{relative}"], cwd=self.private,
                check=True, capture_output=True,
            ).stdout
            entries.append({
                "path": relative, "role": role,
                "sha256": launcher.sha256_bytes(raw), "git_blob": object_id,
                "git_mode": mode,
            })
        if mutate is not None:
            mutate(entries)
        document = {
            "schema_version": 1,
            "oracle_version": launcher.ORACLE_VERSION,
            "manifest_kind": "private_runtime_git_object_execution_closure",
            "entrypoint": launcher.RUNTIME_ENTRYPOINT,
            "entry_count": len(entries),
            "entries": entries,
            "entries_sha256": launcher.sha256_bytes(launcher.canonical_json(entries)),
        }
        document["manifest_sha256"] = launcher.sha256_bytes(
            launcher.canonical_json(document)
        )
        path = self.private / launcher.CLOSURE_MANIFEST_RELATIVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def test_verified_git_object_runtime_launches_in_isolated_mode(self) -> None:
        completed = launcher.launch(self.public, self.private, ["synthetic-check"])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["source"], "verified-git-blob")

    def test_extra_local_module_is_rejected_before_it_can_execute(self) -> None:
        sentinel = self.base / "executed"
        (self.private / "private-oracle/json.py").write_text(
            f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('bad')\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(launcher.PrivateRuntimeLaunchError, "completely clean"):
            launcher.launch(self.public, self.private, ["synthetic-check"])
        self.assertFalse(sentinel.exists())

    def test_untracked_private_file_is_rejected(self) -> None:
        (self.private / "untracked.txt").write_text("unexpected\n", encoding="utf-8")
        with self.assertRaisesRegex(launcher.PrivateRuntimeLaunchError, "untracked"):
            launcher.require_clean_exact_private_final(self.private, self.final)

    def test_private_descendant_is_rejected_even_when_clean(self) -> None:
        (self.private / "tracked.txt").write_text("descendant\n", encoding="utf-8")
        self._commit(self.private, "descendant")
        with self.assertRaisesRegex(launcher.PrivateRuntimeLaunchError, "exact frozen final"):
            launcher.require_clean_exact_private_final(self.private, self.final)

    def test_launch_path_shadowing_is_ignored(self) -> None:
        shadow = self.base / "shadow"
        shadow.mkdir()
        sentinel = self.base / "shadow-executed"
        (shadow / "deterministic_scorer.py").write_text(
            f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('bad')\nSOURCE='bad'\n",
            encoding="utf-8",
        )
        previous = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = str(shadow)
        try:
            completed = launcher.launch(self.public, self.private, ["synthetic-check"])
        finally:
            if previous is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = previous
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["source"], "verified-git-blob")
        self.assertFalse(sentinel.exists())

    def test_manifest_missing_extra_mode_and_digest_mismatches_are_rejected(self) -> None:
        mutations = (
            lambda entries: entries.pop(),
            lambda entries: entries.append(dict(entries[-1], path="private-oracle/extra.py")),
            lambda entries: entries[0].update({"git_mode": "100755"}),
            lambda entries: entries[0].update({"sha256": "0" * 64}),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self._git(self.private, "reset", "--hard", self.final)
                self._write_manifest(mutation)
                self._commit(self.private, "invalid closure")
                bad_final = self._git(self.private, "rev-parse", "HEAD")
                digest = launcher.sha256_bytes(
                    (self.private / launcher.CLOSURE_MANIFEST_RELATIVE_PATH).read_bytes()
                )
                with self.assertRaises(launcher.PrivateRuntimeLaunchError):
                    launcher.validate_manifest(self.private, bad_final, digest)

    def test_staged_missing_extra_mode_and_byte_drift_are_rejected(self) -> None:
        manifest, raw = launcher.validate_manifest(
            self.private, self.final, self.manifest_sha256
        )
        for kind in ("missing", "extra", "mode", "bytes"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(
                prefix="deliver-v1233-stage-", dir="/private/tmp"
            ) as temporary:
                stage = Path(temporary)
                launcher.stage_closure(self.private, self.final, manifest, raw, stage)
                target = stage / manifest["entries"][0]["path"]
                if kind == "missing":
                    target.unlink()
                elif kind == "extra":
                    (stage / "extra.py").write_text("bad\n", encoding="utf-8")
                elif kind == "mode":
                    target.chmod(0o755 if target.stat().st_mode & 0o111 == 0 else 0o644)
                else:
                    target.write_bytes(b"drift\n")
                with self.assertRaises(launcher.PrivateRuntimeLaunchError):
                    launcher.validate_staged_closure(stage, manifest, raw)


if __name__ == "__main__":
    unittest.main()
