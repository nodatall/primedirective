#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Emit Alfred Script Filter JSON for Prime Directive skills and presets."
    )
    parser.add_argument(
        "--skills-dir",
        default=str(repo_root / "skills"),
        help="Path to the root skills directory.",
    )
    parser.add_argument(
        "--presets-file",
        default=str(repo_root / "skills" / "presets.json"),
        help="Path to optional Alfred preset metadata.",
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
        help="Optional Alfred query string. Alfred performs filtering.",
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


def shorten(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def load_skill_meta(skill_dir: Path) -> Optional[dict[str, str]]:
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        return None

    text = skill_path.read_text(encoding="utf-8")
    front_matter = parse_front_matter(text)
    skill_name = front_matter.get("name", skill_dir.name)
    return {
        "kind": "skill",
        "skill": skill_name,
        "title": humanize_skill(skill_name),
        "subtitle": shorten(front_matter.get("description", "")) or "Skill",
        "paste": f"${skill_name}",
        "match": " ".join(
            filter(
                None,
                [
                    skill_name,
                    humanize_skill(skill_name),
                    front_matter.get("description", ""),
                    str(skill_path),
                ],
            )
        ),
    }


def load_skills(skills_dir: Path) -> list[dict[str, str]]:
    items = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill = load_skill_meta(child)
        if skill is not None:
            items.append(skill)
    return items


def load_presets(presets_file: Path, skills: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    if not presets_file.exists():
        return []

    data = json.loads(presets_file.read_text(encoding="utf-8"))
    raw_presets = data.get("presets", [])
    presets = []
    for preset in raw_presets:
        if not isinstance(preset, dict):
            continue
        skill_name = preset.get("skill")
        paste = preset.get("paste")
        if not isinstance(skill_name, str) or not isinstance(paste, str):
            continue
        if skill_name not in skills:
            continue
        base_skill = skills[skill_name]
        title = preset.get("title") or f"{base_skill['title']} Preset"
        subtitle = preset.get("subtitle") or "Preset"
        presets.append(
            {
                "kind": "preset",
                "skill": skill_name,
                "title": title,
                "subtitle": subtitle,
                "paste": paste,
                "match": " ".join(
                    filter(
                        None,
                        [
                            title,
                            subtitle,
                            paste,
                            skill_name,
                            base_skill.get("subtitle", ""),
                        ],
                    )
                ),
            }
        )
    return presets


def build_alfred_items(items: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    alfred_items = []
    for index, item in enumerate(items, start=1):
        subtitle = f"{item['kind'].title()} | {item['subtitle']}"
        alfred_items.append(
            {
                "uid": f"{index}:{item['kind']}:{item['skill']}",
                "title": item["paste"],
                "subtitle": subtitle,
                "arg": item["paste"],
                "match": item["match"],
                "text": {
                    "copy": item["paste"],
                    "largetype": item["paste"],
                },
                "variables": {
                    "kind": item["kind"],
                    "skill": item["skill"],
                    "paste_text": item["paste"],
                },
            }
        )
    return {"items": alfred_items}


def render_list(items: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{item['kind']}\t{item['skill']}\t{item['paste']}\t{item['subtitle']}" for item in items
    )


def main() -> int:
    args = parse_args()
    skills_dir = Path(args.skills_dir).resolve()
    presets_file = Path(args.presets_file).resolve()

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}", file=sys.stderr)
        return 1

    skill_items = load_skills(skills_dir)
    skill_map = {item["skill"]: item for item in skill_items}
    items = skill_items + load_presets(presets_file, skill_map)

    if args.format == "list":
        print(render_list(items))
        return 0

    print(json.dumps(build_alfred_items(items), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
