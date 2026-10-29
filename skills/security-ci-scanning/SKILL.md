---
name: security-ci-scanning
description: >
  Use when asked to add security scanning to CI, wire up a vulnerability scanner
  such as Dependabot, CodeQL, Semgrep, OWASP ZAP or StackHawk, or automate what
  security-code-review does by hand. Sets up automated security scanning in a
  CI/CD pipeline: dependency (SCA) audits, static (SAST) scanning, and dynamic
  (DAST) scanning of a running API or web app. Do not use for a one-off manual
  code review (security-code-review) or for infrastructure and network
  configuration.
---

# Security CI Scanning

Stance: scanning should match what the repository actually is; a library gets dependency and static scanning, a deployed API or web app also gets dynamic scanning. Every setup is a pull request the user reviews, never a direct push, and every required secret is named, never guessed.

## Hard rules

- Never commit directly to the default branch for a scanning setup. Mechanism: open a pull request and let the user merge it. Reason: a CI change is visible to the whole team and must be reviewed like any other.
- Never invent a host, API key, or secret value. Mechanism: leave a clearly marked TODO and name exactly which secret the user must add, and where. Reason: a guessed value that looks plausible is worse than an obvious gap.
- Do not set up dynamic scanning against a repository with no server or API surface. Mechanism: check for server/API framework code, routes and a deployment config first. Reason: DAST testing a library produces false reassurance, not findings.
- State plainly when a detected host, framework or auth type is uncertain, and offer the user a choice instead of picking one silently. Mechanism: list what was detected and what still needs input in the pull request description. Reason: a wrong guess here breaks the pipeline rather than just under-scanning.
- Act only on what the user asked. Before answering or changing anything, open the relevant files and check what is already done; report only what you checked, never guess, and do not redo finished work. Reason: guesses and repeated work waste the user's credit.

## Agent dispatch

Before handling a request, follow the agent selection in [security-specialist](../security-specialist/SKILL.md), including when this skill is invoked directly. Give the selected agent this skill's instructions. If no agent is available, continue yourself.

## Gate

| Situation | Action |
|---|---|
| The repository has no server, API or deployment code (a library, a docs site, pure infrastructure-as-code) | Dependency and static scanning only; explain that dynamic scanning does not apply |
| The repository runs a web server or exposes an API | All three: dependency, static and dynamic scanning |
| A scanning config already exists | Offer to review or update it, do not create a second one |
| The host, auth method or a required secret cannot be detected | Mark it as a TODO in the generated config and the pull request description; never guess a value |

Reason: dynamic scanning needs a running application to attack; pointing it at a library produces nothing but noise.

## Steps

1. **Assess attack surface.** Look for server or API framework code, a Dockerfile or deployment config, route or controller definitions, an OpenAPI or GraphQL schema, and authentication code. Decide from the Gate table whether dynamic scanning applies.
2. **Add dependency (SCA) scanning.** Prefer the ecosystem's own tool or a hosted one already common for it (`npm audit` or Dependabot/Renovate for Node, `pip-audit` for Python, Dependabot for most ecosystems). Fail the build on a high-severity result; see [ci-workflow-patterns.md](references/ci-workflow-patterns.md).
3. **Add static (SAST) scanning.** Wire up a scanner appropriate to the language (for example CodeQL or Semgrep) as a CI job, or rely on `security-code-review` run on each pull request if the team prefers an AI-reasoning review over a pattern-matching tool. State which approach was chosen and why.
4. **Add dynamic (DAST) scanning, if it applies.** Detect the framework, language, likely host pattern (localhost port, Docker service name, a deployed URL) and authentication mechanism. Generate the scanner's configuration file and a CI workflow that starts the app and runs the scan against it. Mark anything undetected as a TODO rather than guessing.
5. **Open it as a pull request**, never a direct commit to the default branch. Describe what was detected, what is ready to use, and exactly which secrets the user must add in their CI provider's settings before the workflow can run.
6. **Verify.** If the new workflow can be run locally or in a sandboxed CI run, do so and report the result. If it cannot be run from here, say so explicitly rather than claiming it works.

## References

- [ci-workflow-patterns.md](references/ci-workflow-patterns.md): example GitHub Actions jobs for dependency, static and dynamic scanning, and the pull request description template.

## Next

- The manual review this automates: [security-code-review](../security-code-review/SKILL.md)
- Back to [security-specialist](../security-specialist/SKILL.md)
