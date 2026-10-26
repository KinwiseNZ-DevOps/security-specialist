#!/usr/bin/env python3
"""Bump the plugin version everywhere it is written, and roll the changelog. Stdlib only.

  python scripts/bump_version.py patch          # 0.1.0 -> 0.1.1
  python scripts/bump_version.py minor          # 0.1.0 -> 0.2.0
  python scripts/bump_version.py major          # 0.1.0 -> 1.0.0
  python scripts/bump_version.py 2.3.4          # set an exact version
  python scripts/bump_version.py patch --dry-run

Claude Code and ChatGPT use their respective plugin manifests to identify a
release. This script updates both manifests, the Claude marketplace entry when
it carries a version, and the "Unreleased" changelog notes.
"""

import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
PORTABLE_PLUGIN = ROOT / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION_RE = re.compile(r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")')
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def bumped(current, how):
    major, minor, patch = (int(x) for x in current.split("."))
    if how == "major":
        return f"{major + 1}.0.0"
    if how == "minor":
        return f"{major}.{minor + 1}.0"
    if how == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if SEMVER_RE.match(how):
        return how
    sys.exit(f"ERROR: '{how}' is not major, minor, patch or an exact X.Y.Z version")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 1:
        print(__doc__)
        return 2
    text = PLUGIN.read_text(encoding="utf-8")
    match = VERSION_RE.search(text)
    if not match:
        sys.exit("ERROR: no semantic version found in .claude-plugin/plugin.json")
    old, new = match.group(2), bumped(match.group(2), args[0])
    if new == old:
        sys.exit(f"ERROR: version is already {old}")
    edits = {
        PLUGIN: VERSION_RE.sub(
            lambda m: f"{m.group(1)}{new}{m.group(3)}", text, count=1
        )
    }
    if PORTABLE_PLUGIN.exists():
        portable = PORTABLE_PLUGIN.read_text(encoding="utf-8")
        if VERSION_RE.search(portable):
            edits[PORTABLE_PLUGIN] = VERSION_RE.sub(
                lambda m: f"{m.group(1)}{new}{m.group(3)}", portable, count=1
            )
    if MARKETPLACE.exists():
        market = MARKETPLACE.read_text(encoding="utf-8")
        if VERSION_RE.search(market):
            edits[MARKETPLACE] = VERSION_RE.sub(
                lambda m: f"{m.group(1)}{new}{m.group(3)}", market
            )
    if CHANGELOG.exists():
        log = CHANGELOG.read_text(encoding="utf-8")
        heading = f"## [{new}] - {datetime.date.today().isoformat()}"
        if "## [Unreleased]" in log:
            log = log.replace("## [Unreleased]", f"## [Unreleased]\n\n{heading}", 1)
        else:
            log = log.rstrip("\n") + f"\n\n{heading}\n"
        edits[CHANGELOG] = log
    for path, content in edits.items():
        print(
            f"{'would update' if dry else 'updated'} {path.relative_to(ROOT).as_posix()}"
        )
        if not dry:
            path.write_text(content, encoding="utf-8", newline="\n")
    print(f"version {old} -> {new}")
    if not dry:
        print(
            "Next: run `python scripts/skills_tool.py check`, commit, then tag the commit v"
            + new
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
