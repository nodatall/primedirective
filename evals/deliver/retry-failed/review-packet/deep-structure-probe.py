from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


repo = Path(sys.argv[1]).resolve()
unknown: object = "leaf"
for _ in range(1500):
    unknown = [unknown]
state = {
    "version": 1,
    "unknown": unknown,
    "jobs": [{"id": "job", "status": "failed", "attempts": 0}],
}
with tempfile.TemporaryDirectory() as directory:
    state_path = Path(directory) / "state.json"
    sys.setrecursionlimit(5000)
    original = (json.dumps(state, separators=(",", ":")) + "\n").encode()
    state_path.write_bytes(original)
    result = subprocess.run(
        [sys.executable, "-m", "queuectl.cli", "retry-failed", str(state_path), "--json"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2, result
    assert result.stdout == b"", result.stdout
    assert b"Traceback" not in result.stderr, result.stderr
    assert state_path.read_bytes() == original
