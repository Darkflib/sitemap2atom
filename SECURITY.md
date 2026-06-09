# Security Policy

## Supported versions

sitemap2atom is currently pre-1.0. Security fixes are applied to the latest
released version on PyPI.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a vulnerability

Please **do not** report security vulnerabilities through public GitHub issues.

Instead, report them privately via one of:

- GitHub's [private vulnerability reporting](https://github.com/darkflib/sitemap2atom/security/advisories/new)
  ("Report a vulnerability" on the Security tab), or
- email to **darkflib@gmail.com**.

Please include a description of the issue, steps to reproduce, and the impact
you anticipate. You can expect an acknowledgement within a few days. Once the
issue is confirmed and fixed, a new release will be published and the reporter
credited (unless anonymity is requested).

## Scope

sitemap2atom fetches arbitrary URLs listed in a sitemap and parses the returned
HTML. Treat sitemaps and the pages they reference as untrusted input, and run
the tool against sources you trust.
