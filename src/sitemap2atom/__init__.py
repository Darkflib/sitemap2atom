"""sitemap2atom: convert an XML sitemap into an enriched Atom feed."""

__version__ = "0.1.1"

from .core import (
    SitemapError,
    enrich_atom_entry,
    enrich_url_list_to_atom,
    extract_metadata,
    feed_to_pretty_xml,
    fetch_sitemap_urls,
    parse_metadata,
    parse_sitemap,
)

__all__ = [
    "__version__",
    "SitemapError",
    "enrich_atom_entry",
    "enrich_url_list_to_atom",
    "extract_metadata",
    "feed_to_pretty_xml",
    "fetch_sitemap_urls",
    "parse_metadata",
    "parse_sitemap",
]
