# Contributing to sitemap2atom

Thanks for your interest in improving sitemap2atom! Contributions of all kinds
are welcome — bug reports, feature ideas, documentation fixes, and pull requests.

## Reporting issues

Please open an issue on the
[issue tracker](https://github.com/darkflib/sitemap2atom/issues) and include:

- What you expected to happen and what actually happened.
- The command you ran (and the sitemap URL, if it can be shared).
- Your Python version and operating system.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/darkflib/sitemap2atom.git
cd sitemap2atom
uv sync            # create the virtualenv and install runtime + dev deps
```

Run the CLI locally without installing it globally:

```bash
uv run sitemap2atom https://example.com/sitemap.xml --limit 5
```

## Tests, linting, and types

The test suite is offline (no network access needed) and must stay that way so
it can run in CI:

```bash
uv run pytest                 # run the tests
uv run flake8 src tests       # lint
uv run black --check src tests
uv run isort --check src tests
uv run mypy src               # type-check
```

Please make sure tests and lint pass before opening a pull request, and add
tests for any new behaviour.

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Make your change, with tests and documentation as appropriate.
3. Add an entry to the **Unreleased** section of [CHANGELOG.md](CHANGELOG.md).
4. Open a pull request describing the change and the motivation.

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
