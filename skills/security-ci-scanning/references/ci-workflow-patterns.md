# CI workflow patterns for security scanning

Examples for GitHub Actions; the same three jobs translate to any other CI provider.

## Dependency (SCA) scanning

The simplest option is often a hosted one that needs no workflow file at all: GitHub's own Dependabot (`.github/dependabot.yml`) opens pull requests for outdated or vulnerable dependencies without a CI job. Where a blocking CI check is wanted instead:

```yaml
name: Dependency audit
on: [pull_request, push]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm audit --audit-level=high
```

Swap the setup and audit steps for the ecosystem in use: `pip-audit` for Python, `bundler-audit` for Ruby, `govulncheck` for Go, `cargo audit` for Rust, `composer audit` for PHP. These audit packages only. To catch an outdated language runtime or base image, add a check that the Dockerfile `FROM` tag or the version file is on a supported release, or use an image scanner; see [runtime-and-platform-advisories.md](../../security-code-review/references/runtime-and-platform-advisories.md).

## Static (SAST) scanning

CodeQL, as a GitHub-native option:

```yaml
name: CodeQL
on: [pull_request, push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions: { security-events: write }
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with: { languages: javascript }
      - uses: github/codeql-action/analyze@v3
```

Semgrep is a lighter-weight, multi-language alternative with its own GitHub Action. Either is a pattern-matching scanner; it complements, rather than replaces, a reasoning-based review such as `security-code-review` run on the diff of a pull request.

## Dynamic (DAST) scanning

A DAST scanner needs the application actually running. The shape is the same regardless of which scanner is used (OWASP ZAP and StackHawk are two common options):

```yaml
name: DAST scan
on: [pull_request, push]
jobs:
  dast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Install dependencies and start the application here, in the
      # background, against the port the scan config below targets.
      - name: Start the application
        run: |
          npm ci
          npm run start &
          npx wait-on http://localhost:3000
      - name: Run the DAST scan
        uses: <scanner-action>@<version>
        with:
          apiKey: ${{ secrets.DAST_API_KEY }}
          # or, for a self-hosted scanner such as ZAP, point it at the
          # running host directly and skip the apiKey input.
```

A scanner's own configuration file (for example `stackhawk.yml` or a ZAP context file) names the target host, any authentication the scan should use, and which paths to include or exclude. Detect the host from `localhost:PORT` patterns in development scripts, Docker Compose service names, or a known deployment URL; if none is clear, default to a placeholder host with a TODO comment rather than guessing.

## Pull request description template

```
## Automated security scanning setup

This PR adds [dependency / static / dynamic] security scanning to CI.

### What was detected
- Framework: <detected framework>
- Language: <detected language>
- Host pattern: <detected host, or "not detected, see TODO">
- Authentication: <detected type, or "not detected, see TODO">

### Ready to use
- <each config or workflow file added>

### Needs your input
- Add these secrets under Settings > Secrets and variables > Actions:
  - `<SECRET_NAME>`: <what it is and where to get it>
- TODOs left in the generated config: <list each one and its file/line>

### Next steps
1. Review the generated configuration and workflow files
2. Add the required secrets
3. Resolve any TODOs
4. Merge; scans then run automatically on future pull requests
```
