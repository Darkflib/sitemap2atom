"""Offline unit tests for sitemap2atom.core (no network access required)."""

from pathlib import Path

import pytest

from sitemap2atom.core import (
    enrich_atom_entry,
    enrich_url_list_to_atom,
    parse_metadata,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample.html"
SAMPLE_URL = "https://example.com/articles/hello"


@pytest.fixture
def sample_html():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_metadata_prefers_opengraph(sample_html):
    meta = parse_metadata(sample_html, SAMPLE_URL)

    # OpenGraph wins over the <title>/Twitter fallbacks.
    assert meta["title"] == "The OpenGraph Title"
    assert meta["description"] == "An OpenGraph description of the page."
    assert meta["site_name"] == "Example News"
    # Relative image is resolved against the page URL.
    assert meta["image"] == "https://example.com/images/cover.jpg"


def test_parse_metadata_collects_namespaced_tags(sample_html):
    meta = parse_metadata(sample_html, SAMPLE_URL)

    assert meta["opengraph"]["type"] == "article"
    assert meta["twitter"]["creator"] == "@janeauthor"
    assert meta["twitter"]["site"] == "@examplenews"
    # `article:*` tags are captured with their full key (the `og:` prefix is
    # stripped, but `article:` is not) so enrich_atom_entry can find them.
    assert meta["opengraph"]["article:author"] == "Jane Author"
    assert meta["opengraph"]["article:published_time"] == "2026-01-15T09:30:00Z"
    assert meta["opengraph"]["article:modified_time"] == "2026-01-16T12:00:00Z"


def test_parse_then_enrich_emits_dates_and_author(sample_html):
    # End-to-end over the fixture: parsing now feeds article:* metadata into
    # the entry, so published/updated dates and the real author appear.
    meta = parse_metadata(sample_html, SAMPLE_URL)
    entry = enrich_atom_entry(meta)

    assert entry.find("author/name").text == "Jane Author"
    assert entry.find("published").text.startswith("2026-01-15")
    assert entry.find("updated").text.startswith("2026-01-16")


def test_parse_metadata_falls_back_to_title_and_netloc():
    html = "<html><head><title>Just a Title</title></head><body></body></html>"
    meta = parse_metadata(html, "https://fallback.test/page")

    assert meta["title"] == "Just a Title"
    assert meta["description"] is None
    assert meta["image"] is None
    # No og:site_name / twitter:site -> falls back to the host.
    assert meta["site_name"] == "fallback.test"


def test_enrich_atom_entry_has_required_elements():
    # Drives the enrichment logic in isolation with metadata that includes
    # article:* fields, independent of how parse_metadata collects tags.
    meta = {
        "url": SAMPLE_URL,
        "title": "The OpenGraph Title",
        "description": "An OpenGraph description of the page.",
        "image": "https://example.com/images/cover.jpg",
        "site_name": "Example News",
        "opengraph": {
            "type": "article",
            "article:author": "Jane Author",
            "article:published_time": "2026-01-15T09:30:00Z",
            "article:modified_time": "2026-01-16T12:00:00Z",
        },
        "twitter": {},
    }
    entry = enrich_atom_entry(meta)

    assert entry.tag == "entry"
    assert entry.find("title").text == "The OpenGraph Title"
    assert entry.find("summary").text == "An OpenGraph description of the page."
    # Author is required by the Atom spec and always emitted.
    assert entry.find("author/name").text == "Jane Author"

    # An alternate link to the original content must be present.
    rels = {link.get("rel") for link in entry.findall("link")}
    assert "alternate" in rels
    assert "enclosure" in rels  # the image

    # og:type becomes a category.
    assert entry.find("category").get("term") == "article"

    # Dates from article:* metadata.
    assert entry.find("published").text.startswith("2026-01-15")
    assert entry.find("updated").text.startswith("2026-01-16")


def test_enrich_atom_entry_author_falls_back_to_site_name():
    meta = {"url": "https://x.test/a", "site_name": "X News", "title": "T"}
    entry = enrich_atom_entry(meta)
    assert entry.find("author/name").text == "X News"


def test_enrich_url_list_to_atom_empty_feed_is_valid():
    feed = enrich_url_list_to_atom([], feed_title="My Feed")

    assert feed.tag == "feed"
    assert feed.get("xmlns") == "http://www.w3.org/2005/Atom"
    assert feed.find("title").text == "My Feed"
    assert feed.find("id").text.startswith("urn:uuid:")
    assert feed.find("updated") is not None

    self_links = [
        link for link in feed.findall("link") if link.get("rel") == "self"
    ]
    assert len(self_links) == 1
    # No URLs were supplied, so there should be no entries.
    assert feed.findall("entry") == []
