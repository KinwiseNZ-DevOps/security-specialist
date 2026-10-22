# Runtime and platform advisories

Contents: why this check exists, where the runtime version hides, how to judge exposure, how to report, dated advisory entries.

A project can have clean code and clean packages and still be exposed because the language runtime, the web server module or the base image underneath it has a vulnerability. Package audits such as `npm audit`, `pip-audit` and `composer audit` check libraries, not the interpreter. Check the runtime separately.

## Where the runtime version hides

Look for it in all of these; they can disagree, and the one that runs in production is the one that counts.

- Version constraints: `composer.json` (`require.php`), `.php-version`, `.tool-versions`, `runtime.txt`, `.nvmrc`, `go.mod`, `pyproject.toml`.
- Container files: the `FROM` line of every Dockerfile and the image tags in Compose files and deployment manifests. Note whether a tag is pinned or floating (`latest`, a bare major version).
- CI files: setup actions and matrix versions (for example a PHP setup step).
- Hosting config: platform runtime settings for App Runner, Elastic Beanstalk, shared hosting panels, or a `Procfile`.
- How PHP runs: Apache with `mod_php`, PHP-FPM, or the CLI. Exposure can differ by SAPI.

If the production runtime cannot be seen from the repository, say so. Do not assume the file and the server match.

## Judging exposure

- A version at or above the fixed release on the same branch is not affected by that advisory.
- A version below the fixed release is probably affected, but the advisory may not list affected ranges. Rate confidence Medium until the vendor's own advisory confirms the range.
- A branch that no longer receives updates (end of life) cannot get the fix from the project. Flag it even when the advisory does not name it. Distribution and long-term-support vendors sometimes backport fixes, so the version string alone does not prove exposure: a distribution package can carry the fix under an older version number. Ask for the package changelog or the vendor's advisory page before rating High.
- A floating image tag can be old or new depending on when it was last pulled. Report the tag and ask for the running image's actual version.
- Interim mitigations in an advisory reduce risk on specific attack paths and do not make an installation safe. Never present a configuration change as a substitute for the update, and never apply one without a person's review.

## How to report

- Name the runtime, the version found, the file and line where it was found, and the advisory it is checked against with the date you read it.
- State separately what was seen (a Dockerfile says a tag) and what was not seen (the version actually running).
- Severity comes from the advisory; confidence comes from how sure you are the vulnerable version is the one running. Keep the two ratings separate, as the report format requires.
- The recommended fix is to move to a fixed release of a supported branch, then rebuild and redeploy images. Propose it; do not edit the files.

## Dated advisory entries

Each entry is a snapshot. Check the current source before reporting.

### PHP security release, 21 October 2026

Read on 22 October 2026 from two places: the PHP Foundation blog post "Today's PHP security release and how we're strengthening PHP security" (21 October 2026) and the php.net news archive entry of the same date. Neither was independently checked against NVD or GitHub advisories.

- Fixed releases: PHP 8.5.12, 8.4.27, 8.3.36 and 8.2.35.
- CVE-2026-109618 (GHSA-w8hw-w9fx-j79w), "RCE via OOM corruption": out-of-memory handling can interrupt PHP while request data is only partly initialised, and request cleanup may then treat it as valid.
- CVE-2026-109619 (GHSA-6wmf-4rv5-p3rp), "RCE via stale global state": request-owned internal state can survive after its memory is freed, and a later request in the same worker may use it.
- Both are described as critical remote code execution. The post says leaked early notices carried a wrong score of 10.0 and the actual score is 9.2; the php.net pre-announcement is quoted as CVSS v4.0 9.2. Treat the score as reported by the vendor.
- Reported exposure: unauthenticated requests on Apache with `mod_php` (before application code runs); also confirmed on PHP-FPM through application-level code paths.
- Affected version ranges: not stated in either source. Do not invent them.
- End of life: the php.net entry says PHP 8.1 and older no longer receive updates from the PHP project, though some distributions and LTS vendors backport fixes.
- Distribution packages: the entry says Linux distributions and LTS vendors received patches in advance, so check the vendor for updated packages. It also warns that the volunteer-maintained `rpms.remirepo.net` repository would not have updates that day and urges switching to distribution packages or building from source; check the entry for the current wording.
- Interim measures listed by the advisory (examples only; the full list is on php.net): `memory_limit=-1`, `session.upload_progress.enabled=0`, and `fatal_error_backtraces=0` on PHP 8.5. They reduce exposure on certain paths and do not make an installation safe.
- Exploitation in the wild: not reported in the sources read. Proof-of-concept material is said to have circulated after an early leak, so treat this as urgent.

What to do when asked "are we covered": find the PHP version in every place above, compare it with the fixed releases for its branch, report unknowns plainly, and recommend the update. Do not claim a system is safe from a version file alone.

Where to check current data: the php.net news archive, the GitHub security advisories for `php/php-src`, OSV.dev, and the distribution's own security tracker.
