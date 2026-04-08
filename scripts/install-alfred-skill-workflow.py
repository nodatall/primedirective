#!/usr/bin/env python3

import plistlib
import shlex
import uuid
import zipfile
from pathlib import Path


BUNDLE_ID = "com.fromdarkness.primedirective.skills"
WORKFLOW_NAME = "Prime Directive Skills"
WORKFLOW_DESCRIPTION = (
    "Browse Prime Directive skill commands from AGENTS and paste them into "
    "the frontmost app."
)
WORKFLOW_VERSION = "0.1.0"
HOTKEY_MOD_CMD = 1_048_576
HOTKEY_MOD_OPT = 524_288
HOTKEY_MOD_CMD_OPT = HOTKEY_MOD_CMD + HOTKEY_MOD_OPT

HOTKEY_UID = "EBECBE6E-DB2D-4E67-ACDF-C3021F8776B1"
SCRIPT_FILTER_UID = "22D1EEC5-1233-4759-806C-AAB1E54B2E05"
CLIPBOARD_UID = "D4FC58FF-6FB7-4CBA-A038-7106E06AE264"


def workflow_root() -> Path:
    return Path(__file__).resolve().parent.parent


def alfred_workflows_dir() -> Path:
    return Path.home() / "Library/Application Support/Alfred/Alfred.alfredpreferences/workflows"


def export_dir() -> Path:
    return workflow_root() / "build" / "alfred"


def script_command(repo_root: Path) -> str:
    router = repo_root / "scripts" / "alfred-skill-router.py"
    agents_file = repo_root / "core" / "AGENTS.core.md"
    skills_dir = repo_root / "core" / "skills"
    return (
        f"/usr/bin/python3 {shlex.quote(str(router))} "
        f"--agents-file {shlex.quote(str(agents_file))} "
        f"--skills-dir {shlex.quote(str(skills_dir))} "
        '"$1"'
    )


def build_plist(repo_root: Path) -> dict:
    return {
        "bundleid": BUNDLE_ID,
        "category": "Tools",
        "connections": {
            HOTKEY_UID: [
                {
                    "destinationuid": SCRIPT_FILTER_UID,
                    "modifiers": 0,
                    "modifiersubtext": "",
                    "vitoclose": 0,
                }
            ],
            SCRIPT_FILTER_UID: [
                {
                    "destinationuid": CLIPBOARD_UID,
                    "modifiers": 0,
                    "modifiersubtext": "",
                    "vitoclose": 0,
                }
            ],
        },
        "createdby": "OpenAI Codex",
        "description": WORKFLOW_DESCRIPTION,
        "disabled": 0,
        "name": WORKFLOW_NAME,
        "objects": [
            {
                "config": {
                    "action": 0,
                    "argument": 0,
                    "focusedappvariable": False,
                    "focusedappvariablename": "",
                    "keychar": "v",
                    "keycode": -1,
                    "keymod": HOTKEY_MOD_CMD_OPT,
                    "leftcursor": False,
                    "modsmode": 0,
                    "relatedAppsMode": 0,
                },
                "type": "alfred.workflow.trigger.hotkey",
                "uid": HOTKEY_UID,
                "version": 2,
            },
            {
                "config": {
                    "alfredfiltersresults": True,
                    "alfredfiltersresultsmatchmode": 1,
                    "argumenttrimmode": 0,
                    "argumenttype": 1,
                    "escaping": 102,
                    "keyword": "",
                    "queuedelaycustom": 3,
                    "queuedelayimmediatelyinitially": True,
                    "queuedelaymode": 0,
                    "queuemode": 1,
                    "runningsubtext": "Loading skill commands...",
                    "script": script_command(repo_root),
                    "scriptargtype": 1,
                    "scriptfile": "",
                    "subtext": "Filter and paste a Prime Directive skill command",
                    "title": "Prime Directive skills",
                    "type": 0,
                    "withspace": True,
                },
                "type": "alfred.workflow.input.scriptfilter",
                "uid": SCRIPT_FILTER_UID,
                "version": 2,
            },
            {
                "config": {
                    "autopaste": True,
                    "clipboardtext": "{query}",
                    "ignoredynamicplaceholders": False,
                    "transient": True,
                },
                "type": "alfred.workflow.output.clipboard",
                "uid": CLIPBOARD_UID,
                "version": 3,
            },
        ],
        "readme": (
            "# Prime Directive Skills\n\n"
            "Hotkey: command + option + v\n\n"
            "This opens a list of the AGENTS skill commands from the current "
            "Prime Directive repo.\n\n"
            "Return: paste the selected command.\n"
            "Command + 1 through Command + 9: paste the visible result in that slot."
        ),
        "uidata": {
            HOTKEY_UID: {"xpos": 40, "ypos": 120},
            SCRIPT_FILTER_UID: {"xpos": 255, "ypos": 120},
            CLIPBOARD_UID: {"xpos": 520, "ypos": 120},
        },
        "userconfigurationconfig": [],
        "variablesdontexport": [],
        "version": WORKFLOW_VERSION,
        "webaddress": "",
    }


def find_existing_workflow_dir(workflows_dir: Path) -> Path | None:
    for info_path in workflows_dir.glob("user.workflow.*/info.plist"):
        try:
            data = plistlib.loads(info_path.read_bytes())
        except Exception:
            continue
        if data.get("bundleid") == BUNDLE_ID:
            return info_path.parent
    return None


def ensure_workflow_dir(workflows_dir: Path) -> Path:
    existing = find_existing_workflow_dir(workflows_dir)
    if existing is not None:
        return existing
    workflow_dir = workflows_dir / f"user.workflow.{str(uuid.uuid4()).upper()}"
    workflow_dir.mkdir(parents=True, exist_ok=False)
    return workflow_dir


def export_workflow_bundle(source_dir: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(source_dir))


def main() -> int:
    repo_root = workflow_root()
    workflows_dir = alfred_workflows_dir()
    workflows_dir.mkdir(parents=True, exist_ok=True)
    workflow_dir = ensure_workflow_dir(workflows_dir)

    plist_path = workflow_dir / "info.plist"
    plist_data = build_plist(repo_root)
    plist_path.write_bytes(plistlib.dumps(plist_data, sort_keys=False))

    readme_path = workflow_dir / "README.txt"
    readme_path.write_text(
        "Prime Directive Skills\n"
        "Hotkey: command + option + v\n"
        "Workflow source: scripts/install-alfred-skill-workflow.py\n",
        encoding="utf-8",
    )

    bundle_path = export_dir() / f"{WORKFLOW_NAME}.alfredworkflow"
    export_workflow_bundle(workflow_dir, bundle_path)

    print(f"Installed workflow: {workflow_dir}")
    print(f"Exported bundle: {bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
