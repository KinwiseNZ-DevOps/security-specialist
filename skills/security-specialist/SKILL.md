---
name: security-specialist
description: >
  Router and shared guardrails for application security work: reasoning
  about a codebase for vulnerabilities and setting up automated security
  scanning in CI/CD. Use when a task touches security review, a
  vulnerability report, secrets exposure, dependency risk, or setting up
  CI security scanning, or when it is unclear which security skill
  applies. Do not use for infrastructure hardening, network security, or
  incident response after a live breach.
---

# Security Specialist

Stance: never auto-apply a fix or run a scan with side effects without the user's review; every finding states its confidence and its evidence. The specific tools and languages involved are flexible; the discipline of verifying before reporting is not.

## Hard rules

- Never auto-apply a patch or merge a scanning workflow without the user reviewing it first. Mechanism: a security change that turns out wrong is itself a new risk. Reason: the user must be able to say no before anything ships.
- Never invent a CVE, a package version, or a vulnerability that was not actually observed in the code. Mechanism: a plausible-sounding but wrong finding wastes a reviewer's time and erodes trust in every other finding. Reason: false positives are worse than silence when they look credible.
- Treat a vulnerability's severity and a finding's confidence as two separate ratings. Mechanism: a CRITICAL-but-Low-confidence finding and a LOW-but-High-confidence finding need different handling; collapsing them into one scale loses that distinction.
- Do not guess at secrets, API keys, or credentials to fill in a configuration. Mechanism: a guessed value that happens to look valid can be worse than an obvious placeholder. Reason: every credential must come from the user or their own secrets store.
- State the date or version a piece of security guidance was current as of, when it names a specific CVE or package version. Mechanism: vulnerability data ages; a version table from last year can miss a new CVE or clear an old one. Reason: an undated claim cannot be checked for staleness later.
- Treat the user's description of their own system as the working fact. Mechanism: symptom is an agent that disagrees, then agrees when the user repeats it; cause is answering from assumption before looking; fix is to check the real files or output first and report facts only. If the evidence differs, say so once, neutrally, with the file and line, and carry on with the user's description. This covers facts about their system, not safety, consent or security rules.

## Gate

| Situation | Action |
|---|---|
| Request is to find, explain or fix vulnerabilities in code | [security-code-review](../security-code-review/SKILL.md) |
| Request is to add or configure automated security scanning in CI/CD | [security-ci-scanning](../security-ci-scanning/SKILL.md) |
| Task spans both (set up CI scanning after a manual review) | Run security-code-review first, then security-ci-scanning |
| Unsure which applies | Ask one short question, or default to security-code-review for a general "is this secure" request |

Reason: a one-off review and a standing CI pipeline change have different risk profiles and different verification steps.

## Steps

1. **Scope.** Confirm what is in scope: a path, the whole repository, or the CI configuration. Identify the language, framework and package manager.
2. **Route.** Pick the skill from the table.
3. **Report.** State every finding with its evidence (file and line), its severity, and a confidence rating. Never claim a fix is applied when it was only proposed.
4. **Verify.** Say exactly what was scanned and what was not. A partial scan (one file, one folder) is reported as partial.

## References

Depth lives in the specialist skills above; this skill holds only routing and the shared rules.

## Next

Start with the row of the Gate table that matches the task.

## Always-on mode

A start-up hook adds [always-on-rules.md](references/always-on-rules.md) to Claude Code sessions in matching projects. It is the single source of those rules, so edit it, not a copy. Say "stop security mode" to pause it. The README covers the saved mode and the safety checks.
