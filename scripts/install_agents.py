#!/usr/bin/env python3
"""Install supplied host agent profiles into an existing project. Stdlib only."""

import argparse
import shutil
import sys
from pathlib import Path

from skills_tool import profile_stem, valid_profile_name

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "resources" / "agents"
HOST_DESTINATIONS = {
    "claude-code": Path(".claude/agents"),
    "github-copilot": Path(".github/agents"),
    "codex": Path("agents/codex"),
}
START = "<!-- installed-skill-agent-routing:start -->"
END = "<!-- installed-skill-agent-routing:end -->"
CODEX_ROUTING = f"""{START}
## Installed skill agent dispatch

When a task matches a role brief in `agents/codex/`, read the matching brief and use it with the relevant skill instructions. Use native subagent delegation when available; otherwise follow the brief directly. Review the result before reporting.
{END}"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        required=True,
        choices=HOST_DESTINATIONS,
        help="Host with a supported native agent profile directory",
    )
    parser.add_argument(
        "--target",
        required=True,
        type=Path,
        help="Existing project directory to receive profiles",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    target = args.target.resolve()
    if not target.is_dir():
        print(f"ERROR: target directory does not exist: {target}")
        return 2

    source_root = AGENTS / args.host
    files = []
    for scope in ("shared", "skill-specific"):
        folder = source_root / scope
        if folder.is_dir():
            files.extend(sorted(path for path in folder.glob("*.md") if path.is_file()))
    if not files:
        print(f"No agent profiles supplied for {args.host}; nothing to install.")
        return 0
    if len(files) > 2:
        print(
            f"ERROR: {args.host} has {len(files)} profiles; supply one main workflow agent and at most one helper."
        )
        return 2
    workflows = [
        path
        for path in files
        if path.parent.name == "skill-specific"
        and profile_stem(path).endswith("-workflow")
    ]
    if len(workflows) != 1:
        print(
            f"ERROR: {args.host} needs exactly one skill-specific main workflow agent ending in -workflow."
        )
        return 2

    skills = ROOT / "skills"
    skill_names = (
        [path.name for path in skills.iterdir() if path.is_dir()]
        if skills.is_dir()
        else []
    )
    invalid_names = []
    for source in files:
        stem = profile_stem(source)
        scope = source.relative_to(source_root).parts[0]
        if not valid_profile_name(stem, scope, skill_names):
            expected = (
                "shared-<role>" if scope == "shared" else "<owning-skill-name>-<role>"
            )
            invalid_names.append(f"{source}: expected {expected}")
    if invalid_names:
        for message in invalid_names:
            print(f"ERROR: {message}")
        return 2

    destination = target / HOST_DESTINATIONS[args.host]

    conflicts = []
    unique_files = {}
    for source in files:
        if source.name in unique_files:
            if source.read_bytes() != unique_files[source.name].read_bytes():
                conflicts.append(f"source profiles have the same name: {source.name}")
            continue
        unique_files[source.name] = source
        installed = destination / source.name
        if installed.exists() and installed.read_bytes() != source.read_bytes():
            conflicts.append(installed)
    if conflicts:
        for path in conflicts:
            print(f"CONFLICT: {path}")
        print("No profiles were installed. Merge conflicting files, then retry.")
        return 1

    routing_path = target / "AGENTS.md"
    routing_text = None
    if args.host == "codex":
        current = (
            routing_path.read_text(encoding="utf-8") if routing_path.exists() else ""
        )
        has_start, has_end = START in current, END in current
        if has_start != has_end:
            print(f"ERROR: incomplete managed routing markers in {routing_path}")
            return 1
        if has_start:
            before, remainder = current.split(START, 1)
            _, after = remainder.split(END, 1)
            routing_text = before.rstrip() + "\n\n" + CODEX_ROUTING + after
        else:
            routing_text = (
                current.rstrip()
                + ("\n\n" if current.strip() else "")
                + CODEX_ROUTING
                + "\n"
            )

    destination.mkdir(parents=True, exist_ok=True)
    installed_count = 0
    for source in unique_files.values():
        installed = destination / source.name
        if installed.exists():
            print(f"SKIP: already installed: {installed}")
            continue
        shutil.copy2(source, installed)
        installed_count += 1

    if routing_text is not None:
        routing_path.write_text(routing_text, encoding="utf-8")

    print(f"Installed {installed_count} profile(s) into {destination}")
    if routing_text is not None:
        print(f"Updated Codex routing in {routing_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
