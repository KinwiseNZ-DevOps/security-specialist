# Changelog

All notable changes to this plugin are listed here, newest first. Add new notes under "Unreleased", and when you cut a release, move them under the new version and update the version in both plugin manifests (`.claude-plugin/plugin.json` and `plugin.json`) by hand, as this repo has no bump script.

## [Unreleased]

## [0.2.0] - 2026-10-23

- Built the security-code-review and security-ci-scanning skills with the security-specialist router.
- Added recurring vulnerability classes for Django and Dart/Flutter.
- Added runtime and platform advisories to security-code-review: how to find and judge the runtime and base image version, a dated entry for the PHP security release of 21 October 2026, `composer audit` in the watchlist and CI patterns, and a rule against judging a runtime from its version string alone.

## [0.1.0] - 2026-10-17

- Initial template scaffold.
