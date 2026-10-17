---
name: example-skill
description: >
  Placeholder skill demonstrating this repository's skill format: the gate,
  steps, hard rule phrasing and reference layout. Use when adding the first real
  skill, so the expected structure is visible. Replace this folder with real
  skills or delete it once real skills exist.
---

# Example Skill

Stance: one paragraph saying what is frozen (invariants, behaviour) and what is flexible (implementation choices).

## Gate

| Situation | Action |
|---|---|
| A small fixed case that gains nothing | Leave it alone |
| A real, evidenced instance of the problem | Proceed to steps |
| Unsure which applies | State it as "likely, needs measurement" |

Reason: checklist-driven refactors are how an agent does unnecessary work. This section forces hesitation.

## Steps

1. **Detect.** The concrete signals to search for (patterns, tool output, file locations that exist in a real project).
2. **Fix.** The least invasive option first, with one minimal code example.
3. **Verify.** What to measure, and compare like for like (same mode, same device, same data).

## Hard rules

- State the rule. Mechanism: symptom, then cause, then fix. Reason: a rule with only a command gets ignored when the situation varies; a rule with a mechanism generalises.

## References

Depth lives in reference files, loaded on demand, one level deep from this file. See [deep-dive.md](references/deep-dive.md).

## Replace me

When the first real skill is ready:

1. Write it from `templates/skill-template/SKILL.md` (frontmatter, gate, steps, hard rules, next-skill links).
2. Add at least 3 behavioural cases to `evals/cases.jsonl` for it.
3. Run `python scripts/skills_tool.py catalogue`, then `python scripts/skills_tool.py check`.
4. Delete this folder and its eval cases. Reason: placeholders in a live catalogue mislead agents into routing to nothing.

## Always-on mode

When the plugin is installed, a start-up hook adds [always-on-rules.md](references/always-on-rules.md) to every Claude Code session. The user can say "stop example mode" to pause it, or ask for the saved mode to be set to on, off or auto. The rules file is the single source of those rules; edit it, not a copy. The same hooks also run safety checks (risky commands, secrets, invented packages, licences, risky code patterns, suspicious pasted prompts, and a reminder when code changed but no checks ran). Each can be switched off in the features file described in the README, and none edits a file on its own.
