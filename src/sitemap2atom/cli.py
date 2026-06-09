"""Command-line interface for sitemap2atom."""

import logging
import sys

import click
import requests

from . import __version__
from .core import (
    DEFAULT_FEED_TITLE,
    enrich_url_list_to_atom,
    feed_to_pretty_xml,
    fetch_sitemap_urls,
)


@click.command()
@click.argument("sitemap_url")
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write the Atom feed to this file (default: stdout).",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Maximum number of sitemap URLs to process (default: all).",
)
@click.option(
    "--feed-title",
    default=DEFAULT_FEED_TITLE,
    show_default=True,
    help="Title for the generated Atom feed.",
)
@click.option(
    "--timeout",
    type=int,
    default=10,
    show_default=True,
    help="Per-request timeout in seconds.",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable info-level logging.")
@click.version_option(__version__, prog_name="sitemap2atom")
def main(sitemap_url, output, limit, feed_title, timeout, verbose):
    """Convert the XML sitemap at SITEMAP_URL into an enriched Atom feed.

    Each URL in the sitemap is fetched and its OpenGraph/Twitter metadata is
    used to build a rich Atom entry (title, summary, image, author, dates).
    """
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        urls = fetch_sitemap_urls(sitemap_url, timeout=timeout)
    except requests.RequestException as e:
        raise click.ClickException(f"Failed to fetch sitemap {sitemap_url}: {e}")

    if limit is not None:
        urls = urls[:limit]

    if not urls:
        raise click.ClickException(f"No <loc> URLs found in sitemap: {sitemap_url}")

    feed = enrich_url_list_to_atom(urls, feed_title=feed_title, timeout=timeout)
    xml = feed_to_pretty_xml(feed)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(xml + "\n")
        click.echo(f"Wrote {output}", err=True)
    else:
        click.echo(xml)


if __name__ == "__main__":
    main()
