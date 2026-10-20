# Vulnerable and high-risk package watchlist

Load this during the dependency audit step. The table below is a dated snapshot, not a live feed: use it as a starting point, then check a current source before reporting a package as clean.

## Where to check current data

- **[OSV.dev](https://osv.dev)**: aggregates advisories for npm, PyPI, crates.io, Go, Maven, RubyGems, NuGet and more. Has a free query API with no key required, at `api.osv.dev/v1/query`: send it a `POST` with a JSON body naming the package, ecosystem and installed version, for example `{"package": {"name": "<name>", "ecosystem": "<ecosystem>"}, "version": "<installed-version>"}`. Prefer this for an automated check against a lock file.
- **[GitHub Advisory Database](https://github.com/advisories)**: the same source Dependabot uses; browsable, and queryable with `gh api graphql` or the REST advisories endpoint.
- **The ecosystem's own audit command**, run against the project's actual lock file rather than a hand-maintained list: `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, `bundler-audit`. These catch anything newer than this file and anything this file does not cover at all.
- **[NVD](https://nvd.nist.gov)**: the authoritative CVE record; use it to confirm details once OSV or GHSA has named a CVE.

State which of these, if any, was actually checked. A finding sourced only from the table below should say so, since it may already be out of date.

## npm / Node.js

| Package | Vulnerable versions | Issue | Safe version |
|---|---|---|---|
| lodash | < 4.17.21 | Prototype pollution | >= 4.17.21 |
| axios | < 1.6.0 | SSRF, open redirect | >= 1.6.0 |
| jsonwebtoken | < 9.0.0 | Algorithm confusion bypass | >= 9.0.0 |
| shelljs | < 0.8.5 | ReDoS | >= 0.8.5 |
| tar | < 6.1.9 | Path traversal | >= 6.1.9 |
| minimist | < 1.2.6 | Prototype pollution | >= 1.2.6 |
| qs | < 6.7.3 | Prototype pollution | >= 6.7.3 |
| express | < 4.19.2 | Open redirect | >= 4.19.2 |
| xml2js | < 0.5.0 | Prototype pollution | >= 0.5.0 |
| fast-xml-parser | < 4.2.4 | ReDoS | >= 4.2.4 |
| semver | < 7.5.2 | ReDoS | >= 7.5.2 |
| tough-cookie | < 4.1.3 | Prototype pollution | >= 4.1.3 |
| vm2 | any | Sandbox escape; deprecated | use `isolated-vm` instead |
| node-fetch | < 2.6.7 | Open redirect | >= 2.6.7 or 3.x |

Also flag, regardless of version: `eval` or `vm.runInContext` inside a dependency's own code, a native addon pulled in from an unknown publisher, and a package with very low weekly downloads required in production code (supply-chain risk).

## Python / pip

| Package | Vulnerable versions | Issue | Safe version |
|---|---|---|---|
| Pillow | < 10.0.1 | Multiple CVEs, buffer overflow | >= 10.0.1 |
| cryptography | < 41.0.0 | OpenSSL vulnerabilities | >= 41.0.0 |
| PyYAML | < 6.0 | Arbitrary code via `yaml.load()` | >= 6.0, and use `safe_load` |
| paramiko | < 3.4.0 | Authentication bypass | >= 3.4.0 |
| requests | < 2.31.0 | Proxy auth info leak | >= 2.31.0 |
| urllib3 | < 2.0.7 | Header injection | >= 2.0.7 |
| Django | < 4.2.16 | Several CVEs | >= 4.2.16 |
| Jinja2 | < 3.1.4 | HTML attribute injection | >= 3.1.4 |

## Java / Maven

| Package | Vulnerable versions | Issue |
|---|---|---|
| log4j-core | 2.0 to 2.14.1 | Log4Shell remote code execution (CVE-2021-44228); CRITICAL |
| log4j-core | 2.15.0 | Incomplete fix; still vulnerable |
| Apache Commons Text | < 1.10.0 | Text4Shell remote code execution (CVE-2022-42889) |
| Jackson-databind | < 2.14.0 | Deserialization vulnerabilities |

## Ruby, Rust and Go

Ruby: `nokogiri` before 1.16.2 (XXE and other issues), `rexml` before 3.2.7 (ReDoS). Rust: check [rustsec.org/advisories](https://rustsec.org/advisories/) directly, since crate advisories move faster than any fixed table. Go: check [pkg.go.dev/vuln](https://pkg.go.dev/vuln/) directly for the same reason; review any dependency on `golang.org/x/crypto` that is more than a few months behind current.

## General red flags, any ecosystem

Flag a dependency that: has had no update in over two years and has open security issues; was deprecated by its own maintainer with a security advisory; is a fork of a known package published by an unfamiliar account (possible takeover); has a name one character off from a popular package (typosquatting, for example `1odash` instead of `lodash`); or was recently transferred to a new owner.
