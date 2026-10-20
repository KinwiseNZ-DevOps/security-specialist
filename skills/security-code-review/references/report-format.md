# Security report format

Use this template for every security-code-review report.

## Header

```
SECURITY REVIEW REPORT

Project: <project name or path>
Scan date: <today's date>
Scope: <files or directories scanned>
Languages detected: <list>
Frameworks detected: <list>
```

## Findings summary table

Show this first, before any individual finding:

```
| Severity  | Findings |
|-----------|----------|
| CRITICAL  | <n>      |
| HIGH      | <n>      |
| MEDIUM    | <n>      |
| LOW       | <n>      |
| INFO      | <n>      |
| TOTAL     | <n>      |

Dependency audit: <n> flagged packages
Secrets scan: <n> exposed credentials
```

## Finding card

Use one card per finding, grouped by category (not by file):

```
[SEVERITY] <vulnerability type>
Confidence: High / Medium / Low

Location: <file path>, line <n>

Vulnerable code:
  <the exact snippet>

Risk (plain words):
  <what an attacker could do with this, including an example attack
  where it helps, such as a crafted URL or payload>

Recommended fix:
  <the corrected code>

Reference: OWASP <category letter and name>, if applicable
```

## Dependency audit section

```
DEPENDENCY AUDIT

HIGH - lodash@4.17.20 (package.json)
  Prototype pollution via zipObjectDeep(); fix: upgrade to >= 4.17.21

MEDIUM - axios@0.27.2 (package.json)
  CSRF via withCredentials; fix: upgrade to >= 1.6.0

INFO - express@4.18.2
  No known CVE found as of this review; a newer version exists, consider updating
```

## Secrets scan section

```
SECRETS AND EXPOSURE SCAN

CRITICAL - hardcoded API key
  File: src/config/database.js, line 12
  Found: a Stripe secret key assigned directly in source

  Action required:
  1. Rotate the key with the provider immediately
  2. Remove it from source code
  3. Load it from an environment variable instead
  4. Confirm the file holding it is covered by .gitignore
  5. Check git history for the same value in an earlier commit, and
     purge it with a history-rewriting tool if found
```

## Patch proposals section

Include this section only for CRITICAL and HIGH findings. State plainly: "Review each patch before applying. Nothing has been changed yet."

```
PATCH PROPOSALS

Patch 1 of <n>: <vulnerability type> in <file>

Before (vulnerable):
  <snippet>

After (fixed):
  <snippet, with a short inline comment on what changed and why>
```

## Footer

```
SCAN COVERAGE
  Files scanned:   <n>
  Lines analysed:  <n>

NEXT STEPS
  1. Address every CRITICAL finding first
  2. Schedule HIGH findings for the current work
  3. Track MEDIUM and LOW findings in the backlog
  4. Consider automated re-scanning in CI/CD (security-ci-scanning)

This is a static, code-reasoning review. It does not run the application
and cannot find every runtime-only vulnerability; pair it with dynamic
testing for fuller coverage.
```

## Confidence ratings

| Confidence | When to use it |
|---|---|
| High | The vulnerability is unambiguous and exploitable as written; no sanitisation is present. |
| Medium | Likely real, but depends on runtime configuration or a call path the review could not fully trace. |
| Low | A suspicious pattern, possibly a false positive; flag it for a human to confirm. |

Never omit the confidence rating; it is what lets a reviewer prioritise their own time.
