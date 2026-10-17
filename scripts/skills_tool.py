#!/usr/bin/env python3
"""Validate skills and keep the README catalogue in sync. Stdlib only.

  python scripts/skills_tool.py validate     # exit 1 on any problem
  python scripts/skills_tool.py catalogue    # rewrite README catalogue block
  python scripts/skills_tool.py check        # validate + fail if catalogue is stale

Plugin manifests in .claude-plugin/, agent profile contents and the manifest agents list are checked on every run. Dashes are always checked in text files outside reference-content/, which holds raw source material. Ship checks for placeholders and setup-only paths in the Git index run once skills/example-skill has been deleted.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
EVALS = ROOT / "evals" / "cases.jsonl"
AGENT_SOURCES = ROOT / "resources" / "agents"
BEGIN, END = "<!-- catalogue:begin -->", "<!-- catalogue:end -->"
BADGE_RE = re.compile(r"(badge/agent_skills-)(\d+|<N>)(-)")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")
ABSOLUTE_RE = re.compile(r"^([A-Za-z]:)?/")
MAX_BODY_LINES, MAX_DESC, MAX_NAME, MIN_EVALS = 500, 1024, 64, 3
BANNED_DASHES = (chr(0x2013), chr(0x2014))
PLACEHOLDER_RE = re.compile(r"<([A-Za-z][^<>\n]*)>")
HTML_TAGS = {"details", "summary", "div", "br", "p", "a", "img", "kbd", "sub", "sup"}
PLACEHOLDER_FILES = (
    "README.md", "LICENSE", "AGENTS.md", "evals/cases.jsonl",
    ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".cfg",
    ".ini", ".sh", ".ps1", ".mjs", ".js", ".ts", ".html", ".css", ".license",
}
PRIVATE_PATHS = ("SETUP.md", "templates", "reference-content")
PLUGIN_DIR = ROOT / ".claude-plugin"
RESERVED_PLUGIN_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
RESERVED_PLUGIN_NAMES = {"claude", "anthropic", "anthropics", "claude-code", "claude-mods"}
MARKETPLACE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
IGNORED_AGENT_FIELDS = ("permissionMode", "hooks", "mcpServers", "initialPrompt")
SKILL_PATH_RE = re.compile(r"skills/[A-Za-z0-9_.-]+/SKILL\.md")


def read_text(path):
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return None


def parse(path):
    text = read_text(path)
    if text is None:
        return None, ""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    fm, key, folded = {}, None, False
    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if top and not line.startswith(" "):
            key, val = top.group(1), top.group(2).strip()
            folded = val in (">", "|")
            fm[key] = "" if folded else val.strip("\"'")
        elif key and line.startswith(" "):
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, m.group(2)


def skill_dirs():
    if not SKILLS.is_dir():
        sys.exit("ERROR: skills/ directory not found")
    return sorted(p for p in SKILLS.iterdir() if p.is_dir())


def link_errors(md):
    text = read_text(md)
    if text is None:
        return []
    errors = []
    for target in LINK_RE.findall(text):
        rel = target.split("#")[0]
        if not rel or ABSOLUTE_RE.match(rel):
            continue
        if not (md.parent / rel).resolve().exists():
            errors.append(f"{md.relative_to(ROOT)}: broken link {target}")
    return errors


def validate():
    errors = []
    names = {p.name for p in skill_dirs()}
    for d in skill_dirs():
        f = d / "SKILL.md"
        if not f.exists():
            errors.append(f"{d.name}: missing SKILL.md")
            continue
        fm, body = parse(f)
        if fm is None:
            errors.append(f"{d.name}: no frontmatter")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if name != d.name:
            errors.append(f"{d.name}: name '{name}' != folder")
        if not NAME_RE.match(name) or len(name) > MAX_NAME:
            errors.append(f"{d.name}: invalid name")
        if not desc or len(desc) > MAX_DESC:
            errors.append(f"{d.name}: description empty or >{MAX_DESC} chars ({len(desc)})")
        if "<" in desc or ">" in desc:
            errors.append(f"{d.name}: description contains angle brackets")
        if not re.search(r"\bUse\b|\bUse when\b", desc):
            errors.append(f"{d.name}: description lacks a 'Use ...' trigger")
        lines = len(body.splitlines())
        if lines > MAX_BODY_LINES:
            errors.append(f"{d.name}: body {lines} lines > {MAX_BODY_LINES}")
        for md in sorted(d.rglob("*.md")):
            errors += link_errors(md)
    for md in (README, AGENTS):
        if md.exists():
            errors += link_errors(md)
    if EVALS.exists():
        counts = {n: 0 for n in names}
        for i, line in enumerate(EVALS.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"evals/cases.jsonl:{i}: invalid JSON")
                continue
            for s in case.get("skills", []):
                if s in counts:
                    counts[s] += 1
                else:
                    errors.append(f"evals/cases.jsonl:{i}: unknown skill {s}")
            if not case.get("query") or not case.get("expected_behavior"):
                errors.append(f"evals/cases.jsonl:{i}: needs query and expected_behavior")
        for n, c in counts.items():
            if c < MIN_EVALS:
                errors.append(f"{n}: {c} eval cases < {MIN_EVALS}")
    else:
        errors.append("evals/cases.jsonl missing")
    return errors


def profile_stem(path):
    return path.name[:-len(".agent.md")] if path.name.endswith(".agent.md") else path.stem


def valid_profile_name(stem, scope, skill_names):
    if scope == "shared":
        return stem.startswith("shared-")
    return any(stem.startswith(f"{name}-") for name in skill_names)


def validate_agent_sources():
    errors = []
    if not AGENT_SOURCES.is_dir():
        return errors
    names = sorted(p.name for p in skill_dirs())
    for host in sorted(path for path in AGENT_SOURCES.iterdir() if path.is_dir()):
        profiles = []
        workflow_profiles = []
        for scope in ("shared", "skill-specific"):
            folder = host / scope
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.md")):
                profiles.append(path)
                stem = profile_stem(path)
                if scope == "skill-specific" and stem.endswith("-workflow"):
                    workflow_profiles.append(path)
                if not valid_profile_name(stem, scope, names):
                    expected = "shared-<role>" if scope == "shared" else "<owning-skill-name>-<role>"
                    errors.append(f"{path.relative_to(ROOT)}: name must use {expected}")
        if len(profiles) > 2:
            errors.append(f"{host.name}: {len(profiles)} agent profiles > 2; combine workflows into one main agent and one helper")
        if profiles and len(workflow_profiles) != 1:
            errors.append(f"{host.name}: supply exactly one skill-specific main profile ending in -workflow")
    return errors


def agent_frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", read_text(path) or "", re.S)
    return m.group(1) if m else None


def agent_skills(frontmatter):
    skills, listing = [], False
    for line in frontmatter.splitlines():
        if re.match(r"^skills:\s*$", line):
            listing = True
            continue
        inline = re.match(r"^skills:\s*(.+)$", line)
        if inline:
            return [s.strip() for s in inline.group(1).strip("[]").split(",") if s.strip()]
        if listing:
            item = re.match(r"^\s+-\s+(\S+)\s*$", line)
            if item:
                skills.append(item.group(1))
            elif line and not line.startswith(" "):
                break
    return skills


def agent_profiles(host):
    for scope in ("shared", "skill-specific"):
        folder = AGENT_SOURCES / host / scope
        if folder.is_dir():
            yield from sorted(folder.glob("*.md"))


def validate_agent_contents():
    errors = []
    if not AGENT_SOURCES.is_dir():
        return errors
    names = {p.name for p in skill_dirs()}
    for host in sorted(p.name for p in AGENT_SOURCES.iterdir() if p.is_dir()):
        for path in agent_profiles(host):
            rel = path.relative_to(ROOT)
            text = read_text(path) or ""
            if SKILL_PATH_RE.search(text):
                errors.append(f"{rel}: refers to skills/<name>/SKILL.md, a path that does not exist in a user's project or an installed plugin. Name the skill and list it under skills: instead")
            if host != "claude-code":
                continue
            fm = agent_frontmatter(path)
            if fm is None:
                errors.append(f"{rel}: Claude Code agent has no frontmatter")
                continue
            for field in IGNORED_AGENT_FIELDS:
                if re.search(rf"^{field}:", fm, re.M):
                    errors.append(f"{rel}: '{field}' is ignored in plugin agents; use plugin hooks or MCP config instead")
            for skill in agent_skills(fm):
                if skill not in names:
                    errors.append(f"{rel}: skills: lists '{skill}', which is not in skills/")
    return errors


def load_json(path):
    try:
        return json.loads(read_text(path) or ""), None
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"{path.relative_to(ROOT)}: invalid JSON ({exc})"


def validate_plugin():
    errors = []
    manifest = PLUGIN_DIR / "plugin.json"
    market = PLUGIN_DIR / "marketplace.json"
    if not manifest.exists():
        return [".claude-plugin/plugin.json missing"]
    data, err = load_json(manifest)
    if err:
        return [err]
    name = data.get("name", "")
    if not isinstance(name, str) or not name:
        errors.append(".claude-plugin/plugin.json: name is required")
        name = ""
    elif "<" not in name:
        if not NAME_RE.match(name):
            errors.append(f".claude-plugin/plugin.json: name '{name}' must be kebab-case")
        if name in RESERVED_PLUGIN_NAMES or name.startswith(RESERVED_PLUGIN_PREFIXES):
            errors.append(f".claude-plugin/plugin.json: name '{name}' is reserved for Anthropic plugins")
    for key in ("version", "description"):
        if not data.get(key):
            errors.append(f".claude-plugin/plugin.json: {key} is required")
    if not (data.get("author") or {}).get("name"):
        errors.append(".claude-plugin/plugin.json: author.name is required")

    first = (read_text(ROOT / "LICENSE") or "").lstrip().splitlines()[:1]
    is_mit = bool(first) and first[0].strip() == "MIT License"
    badge_mit = "license-MIT" in (read_text(README) or "")
    declared = data.get("license", "")
    if not declared:
        errors.append(".claude-plugin/plugin.json: license is required")
    elif (declared == "MIT") != is_mit:
        errors.append(f".claude-plugin/plugin.json: license '{declared}' does not match LICENSE ({'MIT' if is_mit else 'not MIT'})")
    if badge_mit and declared != "MIT":
        errors.append("README.md: MIT licence badge but plugin.json license is not MIT")

    listed = []
    if "agents" in data:
        entries = data["agents"]
        if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
            errors.append(".claude-plugin/plugin.json: agents must be a list of file paths")
            entries = []
        for entry in entries:
            target = (ROOT / entry).resolve()
            if not entry.startswith("./") or not entry.endswith(".md") or ".." in entry:
                errors.append(f".claude-plugin/plugin.json: agents entry '{entry}' must be a ./ path to a .md file inside the repo")
            elif not target.is_file():
                errors.append(f".claude-plugin/plugin.json: agents entry '{entry}' does not exist")
            else:
                listed.append(target)
    for path in agent_profiles("claude-code"):
        if path.resolve() not in listed:
            errors.append(f".claude-plugin/plugin.json: agents must list ./{path.relative_to(ROOT).as_posix()}; without it Claude Code scans agents/ instead")

    top_agents = ROOT / "agents"
    if top_agents.is_dir():
        for md in sorted(top_agents.rglob("*.md")):
            errors.append(f"{md.relative_to(ROOT).as_posix()}: Claude Code scans a top-level agents/ folder; keep Codex briefs only under resources/agents/codex/")

    if not market.exists():
        return errors + [".claude-plugin/marketplace.json missing"]
    mdata, err = load_json(market)
    if err:
        return errors + [err]
    mname = mdata.get("name", "")
    if not mname or ("<" not in mname and not MARKETPLACE_NAME_RE.match(mname)):
        errors.append(".claude-plugin/marketplace.json: name missing or invalid")
    if not (mdata.get("owner") or {}).get("name"):
        errors.append(".claude-plugin/marketplace.json: owner.name is required")
    entries = mdata.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        errors.append(".claude-plugin/marketplace.json: plugins must hold exactly one entry (this repo)")
    else:
        entry = entries[0]
        if entry.get("name") != name:
            errors.append(".claude-plugin/marketplace.json: plugin entry name differs from plugin.json name")
        if entry.get("source") != "./":
            errors.append('.claude-plugin/marketplace.json: plugin entry source must be "./"')
        if entry.get("version") and entry.get("version") != data.get("version"):
            errors.append(".claude-plugin/marketplace.json: entry version differs from plugin.json version")
    return errors


def dashes():
    errors = []
    for p in sorted(ROOT.rglob("*")):
        parts = p.relative_to(ROOT).parts
        if not p.is_file() or ".git" in parts or parts[0] == "reference-content":
            continue
        if any(dash in p.name for dash in BANNED_DASHES):
            errors.append(f"{p.relative_to(ROOT)}: em or en dash in the file name (use a hyphen)")
        text = read_text(p)
        if text is None:
            if p.suffix.lower() in TEXT_EXTENSIONS or p.suffix == "":
                errors.append(f"{p.relative_to(ROOT)}: not UTF-8 text, so dashes cannot be checked")
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if any(dash in line for dash in BANNED_DASHES):
                errors.append(f"{p.relative_to(ROOT)}:{i}: em or en dash (use a hyphen)")
    return errors


def strip_terms():
    f = ROOT / "reference-content" / "strip-terms.txt"
    if not f.exists():
        return []
    terms = [l.strip().lower() for l in f.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.lstrip().startswith("#")]
    if not terms:
        return []
    targets = [ROOT / n for n in ("README.md", "AGENTS.md")]
    for folder in ("skills", "evals", "reference-content/sources"):
        d = ROOT / folder
        if d.is_dir():
            targets += [x for x in d.rglob("*") if x.is_file()]
    errors = []
    for x in targets:
        text = read_text(x)
        if text is None:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for term in terms:
                if term in low:
                    errors.append(f"{x.relative_to(ROOT)}:{i}: project-specific term '{term}' (see strip-terms.txt)")
    return errors


def ship_checks():
    if (SKILLS / "example-skill").exists():
        return [], True
    errors = []
    for rel in PLACEHOLDER_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in PLACEHOLDER_RE.finditer(line):
                inner = m.group(1)
                first = inner.split()[0].lower().rstrip("/")
                if first in HTML_TAGS:
                    continue
                if " " in inner or inner[0].isupper():
                    errors.append(f"{rel}:{i}: leftover placeholder <{inner}>")
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--cached", "--", *PRIVATE_PATHS],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return errors + ["git is not installed, so ship checks could not run"], False
    if tracked.returncode:
        errors.append("could not read the Git index; commit the repository before shipping")
    else:
        errors.extend(
            f"{path}: private setup file is tracked; keep it local and ignored"
            for path in tracked.stdout.splitlines()
        )
    # Checked one path at a time: `git check-ignore --quiet` rejects several paths at once.
    # Only paths that exist are tested, because a directory-only ignore rule cannot match a
    # path that is not there, and a repo with no reference-content/ has nothing to leak yet.
    unignored = []
    for rel in PRIVATE_PATHS:
        if not (ROOT / rel).exists():
            continue
        try:
            result = subprocess.run(
                ["git", "check-ignore", "--quiet", "--no-index", "--", rel],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return errors + ["git is not installed, so ship checks could not run"], False
        if result.returncode != 0:
            unignored.append(rel)
    if unignored:
        errors.append("setup-only paths must be ignored in .gitignore: " + ", ".join(unignored))
    return errors, False


def build_catalogue():
    rows = ["| Skill | Purpose |", "|---|---|"]
    for d in skill_dirs():
        fm, _ = parse(d / "SKILL.md")
        desc = (fm or {}).get("description", "")
        first = re.split(r"(?<=\.)\s", desc, maxsplit=1)[0] if desc else ""
        rows.append(f"| [`{d.name}`](skills/{d.name}/SKILL.md) | {first} |")
    return "\n".join(rows)


def catalogue(write):
    text = README.read_text(encoding="utf-8")
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    new = f"{BEGIN}\n{build_catalogue()}\n{END}"
    if not pat.search(text):
        return ["README.md: catalogue markers missing"]
    updated = pat.sub(lambda _: new, text)
    updated = BADGE_RE.sub(lambda m: f"{m.group(1)}{len(skill_dirs())}{m.group(3)}", updated)
    if updated == text:
        return []
    if write:
        README.write_text(updated, encoding="utf-8")
        return []
    return ["README.md: catalogue stale; run `python scripts/skills_tool.py catalogue`"]


def validate_always_on():
    hooks_dir = ROOT / "hooks"
    config_path = hooks_dir / "always-on.config.json"
    if not hooks_dir.exists() and not config_path.exists():
        return []
    errors = []
    data, err = load_json(config_path)
    if err:
        return [err]
    for key in ("id", "name", "phrase", "rules"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"hooks/always-on.config.json: {key} is required")
    if errors:
        return errors
    rules = ROOT / data["rules"]
    if not rules.is_file():
        errors.append(f"hooks/always-on.config.json: rules file '{data['rules']}' does not exist")
    else:
        text = rules.read_text(encoding="utf-8")
        words = len(text.split())
        if words > 320:
            errors.append(f"{data['rules']}: {words} words; keep always-on rules to 320 or fewer, they are paid for in every session")
        if re.search(r"<[A-Za-z][^<>\n]*>", text):
            errors.append(f"{data['rules']}: leftover placeholder text")
    hooks_json, err = load_json(hooks_dir / "hooks.json")
    if err:
        errors.append(err)
    elif "always-on.mjs" not in json.dumps(hooks_json):
        errors.append("hooks/hooks.json: must run hooks/always-on.mjs")
    if not (hooks_dir / "always-on.mjs").is_file():
        errors.append("hooks/always-on.mjs is missing")
    markers = data.get("autoMarkers", [])
    if not isinstance(markers, list) or not all(isinstance(m, dict) and m.get("file") for m in markers):
        errors.append("hooks/always-on.config.json: autoMarkers must be a list of objects with a file")
    if data.get("defaultMode", "on") not in ("on", "off", "auto"):
        errors.append("hooks/always-on.config.json: defaultMode must be on, off or auto")
    return errors


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    errors = []
    skipped = False
    if cmd in ("validate", "check"):
        errors += validate()
        errors += validate_agent_sources()
        errors += validate_agent_contents()
        errors += validate_plugin()
        errors += validate_always_on()
        errors += dashes()
        errors += strip_terms()
        ship_errors, skipped = ship_checks()
        errors += ship_errors
    if cmd == "catalogue":
        errors += catalogue(write=True)
    if cmd == "check":
        errors += catalogue(write=False)
    if cmd not in ("validate", "catalogue", "check"):
        print(__doc__)
        return 2
    for e in errors:
        print("ERROR:", e)
    note = " [ship checks skipped: example-skill present]" if skipped else ""
    print(f"{cmd}: {'FAILED' if errors else 'ok'} ({len(skill_dirs())} skills){note}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
