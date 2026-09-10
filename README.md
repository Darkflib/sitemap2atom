# sitemap2atom

A simple tool to convert an XML sitemap into an [Atom](https://datatracker.ietf.org/doc/html/rfc4287)
feed — especially useful for sites that don't have a CMS, or where the CMS
doesn't produce a feed. Each URL in the sitemap is fetched and its OpenGraph and
Twitter Card metadata (title, description, image, author, dates) is used to build
a rich Atom entry.

## Installation

### Run without installing (uvx)

Once published to PyPI you can run it directly with
[uv](https://docs.astral.sh/uv/):

```bash
uvx sitemap2atom https://example.com/sitemap.xml -o feed.atom
```

To run the latest code straight from GitHub (before a release, or to try `main`):

```bash
uvx --from git+https://github.com/darkflib/sitemap2atom sitemap2atom https://example.com/sitemap.xml
```

### Install as a tool / library

```bash
uv tool install sitemap2atom      # installs the `sitemap2atom` command
# or
pip install sitemap2atom
```

## Usage

```bash
sitemap2atom SITEMAP_URL [OPTIONS]
```

By default the feed is written to standard output; redirect it or use `-o` to
save it to a file:

```bash
# Print to stdout
sitemap2atom https://example.com/sitemap.xml

# Write to a file, limiting to the first 20 URLs
sitemap2atom https://example.com/sitemap.xml -o feed.atom --limit 20
```

### Options

- `-o, --output PATH` — write the Atom feed to this file (default: stdout).
- `--limit N` — maximum number of sitemap URLs to process (default: all).
- `--feed-title TEXT` — title for the generated feed (default: `Enriched URL Feed`).
- `--timeout SECONDS` — per-request timeout in seconds (default: `10`).
- `-v, --verbose` — enable info-level logging on stderr.
- `--version` — show the version and exit.

### As a library

```python
from sitemap2atom import fetch_sitemap_urls, enrich_url_list_to_atom, feed_to_pretty_xml

urls = fetch_sitemap_urls("https://example.com/sitemap.xml")
feed = enrich_url_list_to_atom(urls[:10], feed_title="My Feed")
print(feed_to_pretty_xml(feed))
```

## Example output

See this gist for a sample of the kind of enriched Atom feed produced:
<https://gist.github.com/Darkflib/989b8f3a5a1ea995e8e294669d5e282a>

## Limitations

This is a simple tool aimed at basic use cases. It does not support
authentication, sitemap index files / pagination, or dynamic sitemaps, and may
not handle every sitemap or page format. Treat the sitemap and the pages it
references as untrusted input and run it against sources you trust.

Some sites sit behind bot-protection that serves a JavaScript "verify your
device" challenge instead of the real content. sitemap2atom sends browser-like
headers, which is enough for many of these, but sites that require JavaScript
execution cannot be fetched by a simple HTTP client. In that case you'll see a
clear error explaining that an HTML page was returned instead of a sitemap.

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/darkflib/sitemap2atom.git
cd sitemap2atom
uv sync
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more, and
[CHANGELOG.md](CHANGELOG.md) for release notes.

## Use Cases

**Editorial pipelines:** Sites without native feeds (static sites, marketing
pages) can now be consumed as structured feeds, ready for newsletter aggregation
or content curation workflows.

**Agent pipelines:** LLM agents and agentic systems need structured, on-demand
inputs. sitemap2atom turns any public web site into machine-readable content
without requiring API keys or custom integrations.

This tool is maintained by [Mike Preston](https://github.com/Darkflib), who
consults on agentic infrastructure at [wwff.tech](https://wwff.tech).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file
for details.

PS. If you do anything interesting with this code, please let me know! I'd love
to hear about it.
