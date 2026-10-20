---
name: security-code-review
description: >
  Reasons about a codebase for security vulnerabilities the way a security
  researcher would: tracing data flow, auditing dependencies and secrets,
  and reporting findings with severity and confidence. Use when asked to
  scan code for vulnerabilities, check for SQL injection, XSS, command
  injection, exposed secrets or insecure dependencies, or review
  authentication and access control logic. Do not use for setting up CI
  scanning pipelines (security-ci-scanning) or for infrastructure and
  network configuration.
---

# Security Code Review

Stance: read code like a researcher, not a pattern-matcher; context, data flow and framework defaults decide whether something is exploitable. Every finding is reported, never silently fixed.

## Agent dispatch

Before handling a request, follow the agent selection in [security-specialist](../security-specialist/SKILL.md), including when this skill is invoked directly. Give the selected agent this skill's instructions. If no agent is available, continue yourself.

## Gate

| Situation | Action |
|---|---|
| No path given | Scan the whole project from its root |
| A path or file is given | Scan only that scope |
| The codebase is clean | Say so clearly, with what was scanned |
| A finding depends on runtime configuration the agent cannot see | Mark its confidence Medium or Low, not High |
| A pattern looks like a secret but matches a known placeholder | Do not flag it (see [secret-patterns.md](references/secret-patterns.md)) |

## Steps

1. **Detect.** Identify the language(s) and framework(s) in use (`package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, `composer.json`). Load the matching section of [language-patterns.md](references/language-patterns.md).
2. **Audit dependencies.** Check lock files against [vulnerable-packages.md](references/vulnerable-packages.md). Flag known CVEs, abandoned packages and suspiciously old pins. State that the watchlist is a snapshot, not a live feed, and that current advisories should be checked for anything it does not cover.
3. **Scan for secrets and exposure.** Check source, config, CI/CD and infrastructure files using [secret-patterns.md](references/secret-patterns.md): hardcoded keys, committed `.env` files, secrets in logs or error responses, cloud credentials.
4. **Scan for vulnerabilities.** Work through [vuln-categories.md](references/vuln-categories.md): injection, authentication and access control, headers, frontend, API, AI/LLM, and logging anti-patterns. Reason about each hit: is sanitisation or a framework default already handling it upstream?
5. **Trace across files.** Follow user-controlled input from its entry point (HTTP params, headers, body, file uploads) to where it is used (queries, `exec` calls, HTML output, file writes). Some vulnerabilities only appear when files are read together.
6. **Verify each finding.** Re-read the code. Downgrade or discard anything that is not genuinely exploitable. Assign severity (CRITICAL, HIGH, MEDIUM, LOW, INFO) and confidence (High, Medium, Low) separately.
7. **Report** in the format in [report-format.md](references/report-format.md): a summary table first, then findings grouped by category with file, line, risk in plain words, and a proposed fix for every CRITICAL and HIGH finding. State: "Review each patch before applying. Nothing has been changed yet."

## Hard rules

- Never auto-apply a proposed patch. Mechanism: present the before and after code, then stop. Reason: the user approves every change to security-relevant code.
- Report severity and confidence separately for every finding, never collapse them into one scale. Mechanism: a reviewer prioritises differently when a CRITICAL finding is only Low confidence. Reason: collapsing the two hides exactly the information a reviewer needs most.
- Do not flag an intentional placeholder as a secret (`<YOUR_API_KEY>`, `process.env.API_KEY`, `sk-...` in a comment). Mechanism: check [secret-patterns.md](references/secret-patterns.md)'s safe-pattern list before flagging. Reason: a noisy scan trains reviewers to ignore it.
- State which files and how much of the codebase were actually scanned. Mechanism: a scan of one file is not a security review of the project. Reason: an unqualified "scanned" claim is indistinguishable from a full audit until it is wrong.
- Treat the vulnerable-packages watchlist and any named CVE as dated reference material, not a live feed. Mechanism: new CVEs appear and old ones get patched continuously. Reason: a stale "no known CVEs" claim is a false negative.

## References

- [vuln-categories.md](references/vuln-categories.md): detection guidance for injection, auth, headers, frontend, API, AI/LLM and logging categories, with OWASP mapping.
- [language-patterns.md](references/language-patterns.md): framework-specific vulnerable patterns for JavaScript/TypeScript, Python, Java, PHP, Go, Ruby, Rust, and Dart/Flutter.
- [secret-patterns.md](references/secret-patterns.md): regex and entropy heuristics for credentials, keys and connection strings, plus safe patterns to not flag.
- [vulnerable-packages.md](references/vulnerable-packages.md): a dated watchlist of known-vulnerable packages by ecosystem.
- [report-format.md](references/report-format.md): the findings summary, finding-card and patch-proposal template.
- [hardening-checklist.md](references/hardening-checklist.md): a quick-reference checklist and templates (security headers, JWT validation, cookie flags) for what a fix should look like.

## Next

- Automate this scanning in CI/CD: [security-ci-scanning](../security-ci-scanning/SKILL.md)
- Back to [security-specialist](../security-specialist/SKILL.md)
