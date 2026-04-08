#!/usr/bin/env python3

import argparse
import json
import re
import sys
from pathlib import Path


TRIGGER_LINE_RE = re.compile(r"^- `(.+?)` -> `(.+?)`$")
OPTIONAL_SEGMENT_RE = re.compile(r"\s*\[[^\]]+\]")
PLACEHOLDER_SEGMENT_RE = re.compile(r'\s*"[^"]*"\s*|\s*<[^>]+>')


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    default_agents_file = repo_root / "AGENTS.md"
    if not default_agents_file.exists():
        default_agents_file = repo_root / "core" / "AGENTS.core.md"

    default_skills_dir = repo_root / "skills"
    if not default_skills_dir.exists():
        default_skills_dir = repo_root / "core" / "skills"

    parser = argparse.ArgumentParser(
        description="Emit Alfred Script Filter JSON for Prime Directive skills."
    )
    parser.add_argument(
        "--agents-file",
        default=str(default_agents_file),
        help="Path to the AGENTS markdown file to parse.",
    )
    parser.add_argument(
        "--skills-dir",
        default=str(default_skills_dir),
        help="Path to the skills directory.",
    )
    parser.add_argument(
        "--format",
        choices=("alfred", "list"),
        default="alfred",
        help="Output format. Use 'list' for terminal inspection.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Optional Alfred query string. Alfred performs the filtering.",
    )
    return parser.parse_args()


def parse_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}

    front_matter = {}
    for raw_line in parts[0].splitlines()[1:]:
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        front_matter[key.strip()] = value.strip()
    return front_matter


def humanize_skill(skill_name: str) -> str:
    return skill_name.replace("-", " ").title()


def load_skill_meta(skill_path: Path, skill_name: str) -> dict[str, str]:
    meta = {
        "name": skill_name,
        "title": humanize_skill(skill_name),
        "description": "",
        "path": str(skill_path),
    }

    if not skill_path.exists():
        return meta

    text = skill_path.read_text(encoding="utf-8")
    front_matter = parse_front_matter(text)
    meta["name"] = front_matter.get("name", skill_name)
    meta["description"] = front_matter.get("description", "")
    return meta


def extract_triggers(agents_file: Path, skills_dir: Path) -> list[dict[str, str]]:
    items = []
    for line in agents_file.read_text(encoding="utf-8").splitlines():
        match = TRIGGER_LINE_RE.match(line.strip())
        if not match:
            continue

        command_template, skill_name = match.groups()
        skill_path = skills_dir / skill_name / "SKILL.md"
        skill_meta = load_skill_meta(skill_path, skill_name)
        items.append(
            {
                "command_template": command_template,
                "skill_name": skill_meta["name"],
                "skill_title": skill_meta["title"],
                "description": skill_meta["description"],
                "skill_path": skill_meta["path"],
            }
        )
    return items


def shorten(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def paste_command(command_template: str) -> str:
    command = OPTIONAL_SEGMENT_RE.sub("", command_template)
    command = PLACEHOLDER_SEGMENT_RE.sub(" ", command)
    command = " ".join(command.split())
    while command.endswith((" in", " with", " from", " on")):
        command = command.rsplit(" ", 1)[0]
    return command


def build_subtitle(item: dict[str, str]) -> str:
    parts = [item["command_template"]]
    if item["description"]:
        parts.append(shorten(item["description"]))
    return " | ".join(parts)


def build_match(item: dict[str, str]) -> str:
    return " ".join(
        filter(
            None,
            [
                item["skill_name"],
                item["skill_title"],
                item["command_template"],
                item["description"],
            ],
        )
    )


def build_alfred_items(items: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    alfred_items = []
    for index, item in enumerate(items, start=1):
        command_template = item["command_template"]
        skill_path = item["skill_path"]
        paste_text = paste_command(command_template)
        alfred_items.append(
            {
                "uid": f"{index}:{item['skill_name']}",
                "title": paste_text,
                "subtitle": build_subtitle(item),
                "arg": paste_text,
                "match": build_match(item),
                "text": {
                    "copy": paste_text,
                    "largetype": paste_text,
                },
                "variables": {
                    "skill": item["skill_name"],
                    "skill_path": skill_path,
                    "command_template": command_template,
                    "paste_text": paste_text,
                },
            }
        )

    return {"items": alfred_items}


def render_list(items: list[dict[str, str]]) -> str:
    lines = []
    for item in items:
        lines.append(f"{item['skill_name']}\t{item['command_template']}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    agents_file = Path(args.agents_file).resolve()
    skills_dir = Path(args.skills_dir).resolve()

    if not agents_file.exists():
        print(f"AGENTS file not found: {agents_file}", file=sys.stderr)
        return 1

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}", file=sys.stderr)
        return 1

    items = extract_triggers(agents_file, skills_dir)
    if args.format == "list":
        print(render_list(items))
        return 0

    print(json.dumps(build_alfred_items(items), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
