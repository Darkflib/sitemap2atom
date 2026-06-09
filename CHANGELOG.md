# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-09

### Added

- Initial public release.
- `sitemap2atom` command-line tool: fetch an XML sitemap and convert its URLs
  into an enriched Atom feed using OpenGraph and Twitter Card metadata.
- CLI options: `--output`, `--limit`, `--feed-title`, `--timeout`, `--verbose`.
- Installable from PyPI and runnable with `uvx sitemap2atom`.
- Offline test suite covering metadata parsing and Atom feed generation.

[Unreleased]: https://github.com/darkflib/sitemap2atom/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/darkflib/sitemap2atom/releases/tag/v0.1.0
