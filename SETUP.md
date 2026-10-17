# Setup checklist

This repo is a scaffold copied from the skills-repo template. Work top to bottom, then delete this file. Nothing below is optional unless marked otherwise.

## 1. Name and identity

- [ ] Update `README.md`, keeping the template's section order and style: render the repo name with the standard FIGlet ANSI Shadow font only (pyfiglet `ansi_shadow`), then add the title and one-liner, badges (set OWNER, REPO and the skill count), principle in the [!IMPORTANT] callout, intro paragraph, "How they fit together" diagram (delete for a single-skill repo), usage phrases, status and footer links. Split long names across lines as needed. Keep every banner line left-aligned with no indent and no trailing spaces; do not centre or widen the font. Keep local setup files out of the public layout block.
- [ ] Update `LICENSE`: replace `<copyright holder>`
- [ ] Fill in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`: replace every `<PLACEHOLDER>`. Name the marketplace `<plugin-name>-marketplace`: a user can register only one marketplace per name, so two repos must not share one. Plugin names must be kebab-case and must not start with `claude-` or `anthropic-`. Set `license` to match `LICENSE`. If the repo is proprietary, replace `LICENSE`, remove the MIT badge and "Licensed under MIT" line from `README.md`, and set `license` accordingly
- [ ] Bump `version` in `plugin.json` for every release; installed users stay on the old version until it changes
- [ ] `AGENTS.md`: the general rules are identical in every repo by design; do not reword them. Adapt only two sections to the new repo: the **Repository map** (canonical sources, generated artefacts, editing rules, each with a reason) and **Known deliberate states** (delete the placeholder line). The verification command `python scripts/skills_tool.py check` is already correct because the template ships the same validator

## 2. Content

- [ ] In the new repo, add `/templates/` to `.gitignore`. The template repo keeps this folder tracked because it contains the starter skill. Keep `/SETUP.md` and `/reference-content/` ignored as configured. Keep all setup files locally, but remove them from the Git index before the first public commit with `git rm --cached --ignore-unmatch SETUP.md templates reference-content`. The validator fails if they are tracked or not ignored.
- [ ] Build the reference content first (pipeline in `reference-content/README.md`): drop originals into `raw/`, list project-specific names in `strip-terms.txt`, convert each item into a general-purpose file in `sources/`, and fill in `BRIEF.md`
- [ ] Build the skills from `BRIEF.md` and `sources/` only, never from `raw/`
- [ ] Design the skill set first: write the list of skills, their scope boundaries, and which skill owns each nearby topic. Scope discipline beats breadth: prefer curation over accumulation
- [ ] Write the first real skill from `templates/skill-template/SKILL.md`
- [ ] Write its description as a trigger contract: what it does, when to use it, keywords users type, and negative triggers for topics owned by sibling skills
- [ ] If skills share constraints or a "voice", put them in one references file and link it from skills, never copy it
- [ ] Add 3+ behavioural cases per skill to `evals/cases.jsonl` (real queries, expected behaviours, at least one refusal case)
- [ ] Set up the always-on mode. Edit `hooks/always-on.config.json` (`id` equals the plugin name, `name`, a short `phrase` for "stop PHRASE mode", `rules` pointing at the router skill, and `autoMarkers` listing the project files that mean the plugin is relevant, or `autoDetect: false` if it applies everywhere). Write 5 to 8 checkable rules in the router skill's `references/always-on-rules.md`, 320 words or fewer, and update the "Always on" section of `README.md`. The hook is on by default, tells the user its state at session start, and the user toggles it with "stop PHRASE mode" or a saved mode file (on, off or auto). The validator fails if the rules file is missing, too long or has placeholders.
- [ ] Replace the starter cases and delete `skills/example-skill/`
- [ ] Inspect `resources/agents/` after the skills and router names are final. If no definitions were supplied, install none and leave agent folders and dispatch instructions out. Supply at most two native profiles per host: one main workflow agent named `<router-skill>-workflow`, plus one focused helper. Put planning, implementation, testing, and review modes in named sections of the main agent rather than creating one agent per skill. Use a `shared-` helper only when the same definition is reused across repos. Wire the router skill to the main workflow agent and describe when to use the helper. List each Claude Code profile in the `agents` array of `plugin.json` (`./resources/agents/claude-code/...md`). In agent bodies, name skills and list them under `skills:`; never write `skills/<name>/SKILL.md` paths, which do not exist in a user's project or an installed plugin. Other hosts receive the skills only. Preserve `resources/agents/` in the shipped repo so the installer can copy profiles into a project.

## 3. Register

```bash
python scripts/skills_tool.py catalogue   # refreshes the README table
python scripts/skills_tool.py check       # must end: ok (N skills), with no "ship checks skipped" note
```

## 4. Ship

- [ ] `git init`, commit, add the origin remote, push (repo name per 1)
- [ ] MIT repos: make the repository **public** (CI minutes are free on public repos and billed on private ones). Proprietary repos: keep it private; users need git access to the repo to add the marketplace
- [ ] Test the plugin locally: `claude plugin validate . --strict`, then `claude --plugin-dir .`
- [ ] Enable Actions in Settings; the workflow runs on pushes to `main` and PRs
- [ ] Set the GitHub "About" description and add topics (`agent-skills` at minimum)
- [ ] Keep the setup files on your computer for future maintenance. Confirm `python scripts/skills_tool.py check` passes before publishing; it confirms setup-only files are ignored and absent from the Git index.

## 5. Do not

- Do not hand-edit the README catalogue between the markers
- Do not add manifests for other platforms until one needs them; `.claude-plugin/` is the only manifest this template ships
- Do not put installed Codex briefs in a top-level `agents/` folder of the repo; Claude Code scans that folder as subagents. Keep briefs in `resources/agents/codex/`
- Do not import project-specific facts into skills; skills read a project's own architecture at runtime
