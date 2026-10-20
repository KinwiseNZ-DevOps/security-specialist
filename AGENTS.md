# AGENTS.md

Agent map and standing rules for this repository. Read this file as policy, not suggestions. Every rule carries its reason: when a situation is not covered, generalise from the reason rather than guessing.

## Ground truth

- Never speculate about code or files you have not opened. If asked about a file, read it before answering. Reason: confident claims about unread files are indistinguishable from truth in review.
- File and directory names are not reliable evidence of what something does. Reason: naming drifts; contents do not.
- Documentation describes intent, not implementation state. Verify in the actual files before reporting status. Reason: docs lag behind code in every repo.

## Scope of changes

- Make the smallest correct change that satisfies the task. Reason: every extra line is extra review burden and extra risk. Concretely, do not:
  - Add docstrings, comments, or type annotations to content you did not change.
  - Add error handling, fallbacks, or caveats for scenarios that cannot happen (e.g. already covered by the validator). Validate at system boundaries only.
  - Create helpers or abstractions for one-time operations, or design for hypothetical requirements.
  - Refactor or "improve" anything beyond what the task asked.
  - Add comments beyond what the code genuinely needs. Keep the codebase mostly clean: comment only where the logic is not self-evident, and keep those comments short. Reason: comments that restate the code rot into lies; the code is read far more often than it is written.
  - Leave useless comments behind. When editing a file, delete comments in the lines you touch that are wrong, outdated, or say nothing the code does not already say. Reason: dead comments accumulate until readers stop trusting every comment, including the useful ones.
- Prefer editing the source of a rule over editing a restatement of it. Reason: copies drift.

## Accuracy and honesty

- Separate observed fact from inference, and mark anything uncertain.
- If a check cannot be run, say so explicitly instead of reporting success.
- Do not claim completion stronger than the evidence; state exactly what was checked.
- Solve the problem, not the test. Behavioural cases measure quality; they do not define it. If a case or check is wrong, say so rather than working around it.

## Verification

Before reporting any change done, run:

```bash
python scripts/skills_tool.py check
```

Checks: frontmatter, name/folder match, description length and trigger, body under 500 lines, every relative link resolves (including README.md and AGENTS.md), agent profile naming with no more than two profiles per host and exactly one `-workflow` main agent, agent `skills:` entries that exist and no `skills/<name>/SKILL.md` paths in agent bodies, plugin manifests valid and consistent with `LICENSE` and the profiles, at least 3 eval cases per skill, catalogue not stale, no project-specific terms from `reference-content/strip-terms.txt`, and no em or en dashes in file names or in any text outside `reference-content/`. Once `skills/example-skill/` is deleted it also fails on leftover `<placeholder>` text and setup-only paths that are tracked by Git or not ignored.

- The tool is necessary but not sufficient for content quality. For new or changed skill body text, also re-read the changed SKILL.md end to end. Reason: a validator checks structure; only reading checks that the instructions still make sense.

## Repository map (fill in as this repo takes shape)

- `skills/<name>/SKILL.md`: the only source of skill content. Folder name equals frontmatter `name`.
- `resources/agents/`: optional, host-native profile sources consumed by `scripts/install_agents.py`. Shared agent names use the `shared-` namespace; skill-specific agent names use `<owning-skill-slug>-<role>`. No `*.agent.md` files for a host means there are no profiles to install for that host.
- `plugin.json`: the portable Agent Plugins manifest for ChatGPT and Codex. `.agents/plugins/marketplace.json` exposes this repo as a local ChatGPT desktop marketplace.
- `.claude-plugin/plugin.json` and `marketplace.json`: the Claude Code plugin manifest and single-plugin marketplace. The `agents` array lists each Claude Code profile under `resources/agents/claude-code/`. Reason: without the key, Claude Code scans a top-level `agents/` folder and would load Codex briefs as subagents.
- `.github/agents/`, `.claude/agents/`, and `agents/codex/`: optional installed host profiles and Codex role briefs in a target project, never in this repo. The installer creates these folders only when it has profiles to copy and never replaces an existing different file.
- New skills follow the house format that existing skills embody: folder name equals frontmatter `name`; frontmatter, gate, steps, hard rules. Reference files hold the detection patterns, language-specific examples, and templates; a `SKILL.md` links to them rather than inlining their depth. Reason: copies drift.
- `SETUP.md`, `templates/`, and `reference-content/` are local setup material that stays ignored and outside the Git index when a repo is published. Reason: the maintainer needs these files for future work, while public commits must exclude bootstrap material and private sources.
- Custom to this repo: the router `security-specialist` links both specialist skills and names the `security-specialist` hook id; the shared hard rules (never auto-apply, rate severity and confidence separately, never guess a secret) live in the router's hard rules and in `always-on-rules.md`, repeated by reference, not copied. The vulnerable-package watchlist in `security-code-review/references/vulnerable-packages.md` is a dated snapshot, not a live feed; say so whenever it is used.

- `hooks/`: the always-on rules and safety checks. `always-on.mjs` loads the rules at session start; `guard.mjs` runs the checks (dangerous commands, secrets, invented packages, licences, risky code patterns, suspicious prompts, a reminder when code changed but no checks ran) and `common.mjs` holds the shared helpers. These three files are identical in every plugin repository; change them in `template` first. `hooks/always-on.config.json` holds the id, name, phrase, rules path, auto-detect markers and per-check defaults, and `skills/security-specialist/references/always-on-rules.md` is the only source of the rules. Keep that file under 320 words. Reason: it is paid for in tokens at the start of every session, and a copy would drift from the skills. Hooks fail open and only ask, warn or add context; they never edit files silently. The saved mode and check overrides live in the user's `~/.claude/.security-specialist.mode` and `.security-specialist.features.json`, never in this repo.

## Irreversible and shared actions

- Proceed freely for local, reversible actions: editing files, running checks, regenerating the catalogue.
- Ask first for anything destructive, hard to undo, or visible to others: deleting branches or history, force-pushes, changing repository visibility, pushing to shared sources. Reason: damage in a public repo cannot be recalled.

## Commit attribution

- Do not add `Co-Authored-By` trailers for AI assistants to commit messages. Add co-author attribution only when the user explicitly requests it. Reason: commit trailers affect GitHub's contributor attribution.

## Known deliberate states (dated)

- 20 October 2026: skills were authored from condensed, generalised public security references (an existing AI code-review workflow, an OWASP-style anti-pattern catalogue, and CI scanning setup guidance), not from a live project; none has been run against a real vulnerability yet. Reason: first draft awaiting real-world testing.
- 20 October 2026: no agent profiles are supplied under `resources/agents/`. Reason: the three skills run directly and a profile was not needed yet.

## Anti-drift close-out

Before reporting done, confirm the change introduced no new local convention (a new section shape, a new file pattern, a divergent description style). If it did, either move it into the shared source or record the approved exception here. Reason: un-owned variations are how a standard silently dissolves.

## Close-out report

Finish every task with these five points, in this order:

1. What changed and why
2. Files changed
3. Validation run, and the result
4. Validation skipped, and why
5. Residual risks

## How to respond

- Reply in paragraphs: flowing prose, one idea per sentence, short paragraphs. Use lists only where the content is genuinely a list (the five-point close-out report, file paths, step sequences).
- Keep replies under 200 words. Go longer only when the user clearly asks for a thorough response. If more depth seems useful, offer it in one short line rather than writing it unprompted. Reason: long replies bury the decision the user needs to make.
- Write in British / New Zealand English throughout: behaviour, colour, organise, initialise, "-ise" endings, NZ date and spelling conventions. Reason: mixed spellings in one reply read as carelessness to a NZ audience.
- Simplify so a 16-year-old high school student could follow it: everyday words first, explain any unavoidable term the first time it appears, one technical term per sentence. Reason: if the explanation needs jargon to be understood, it has not explained anything.
- If the next step is one the user must do themselves (a setting to change, something to install, a click in a website), brief them first: say what is about to happen, what the step is for, and what success will look like. Then give exactly that one step, completely and simply. Reason: handing over five steps at once invites skipped and half-understood steps.
- After each user-side step, stop and wait for the user to say they are done before giving the next step. Do not stack several manual steps in one reply. Reason: one task at a time keeps confirmation honest and lets problems surface at the step that caused them.
- No padding, no restating the question, no caveats that carry no information.
- Skip em dashes and en dashes entirely and always. They are banned in every reply, every file, every commit message, prose and code comments alike. Every dash in text must be a plain hyphen (-). If a hyphen does not fit, use a comma or rewrite the sentence. Reason: nothing justifies an em dash; a banned character that appears anywhere is a single, checkable, zero-tolerance rule.
