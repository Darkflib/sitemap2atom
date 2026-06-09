"""Core sitemap-to-Atom conversion logic.

The functions here are split so that the HTML/XML parsing is pure (no network)
and therefore unit-testable, while the network-facing helpers wrap them.
"""

import logging
import re
import uuid
from datetime import datetime
from urllib.parse import urljoin, urlparse
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

import dateutil.parser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# A browser-like User-Agent; some sites reject the default requests UA.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

ATOM_NS = "http://www.w3.org/2005/Atom"
DEFAULT_FEED_TITLE = "Enriched URL Feed"


def parse_metadata(html, url):
    """Extract Twitter and OpenGraph metadata from an HTML document.

    This is the pure, network-free half of :func:`extract_metadata` and can be
    tested against static HTML.

    Args:
        html (str | bytes): The raw HTML to parse.
        url (str): The URL the HTML came from (used to resolve relative image
            URLs and as a fallback site name).

    Returns:
        dict: Dictionary containing the extracted metadata.
    """
    soup = BeautifulSoup(html, "html.parser")

    metadata = {
        "url": url,
        "title": None,
        "description": None,
        "image": None,
        "site_name": None,
        "twitter": {},
        "opengraph": {},
    }

    # Extract OpenGraph metadata
    # Collect both `og:*` and `article:*` properties. The `og:` prefix is
    # stripped (e.g. og:title -> title), but `article:*` keys are kept intact
    # because enrich_atom_entry() looks them up by their full name
    # (article:published_time, article:modified_time, article:author).
    og_tags = soup.find_all("meta", property=re.compile(r"^(og|article):"))
    for tag in og_tags:
        prop = tag.get("property", "")
        content = tag.get("content", "")
        if not prop or not content:
            continue
        if prop.startswith("og:"):
            prop = prop[len("og:"):]
        metadata["opengraph"][prop] = content

    # Extract Twitter metadata
    twitter_tags = soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
    for tag in twitter_tags:
        name = tag.get("name", "").replace("twitter:", "")
        content = tag.get("content", "")
        if name and content:
            metadata["twitter"][name] = content

    # Populate main fields from OG or Twitter data
    metadata["title"] = (
        metadata["opengraph"].get("title")
        or metadata["twitter"].get("title")
        or (soup.find("title").get_text().strip() if soup.find("title") else None)
    )

    metadata["description"] = (
        metadata["opengraph"].get("description")
        or metadata["twitter"].get("description")
        or (soup.find("meta", attrs={"name": "description"}) or {}).get("content")
    )

    # Handle image URLs (make absolute if relative)
    image_url = metadata["opengraph"].get("image") or metadata["twitter"].get("image")
    if image_url:
        metadata["image"] = urljoin(url, image_url)

    metadata["site_name"] = (
        metadata["opengraph"].get("site_name")
        or metadata["twitter"].get("site")
        or urlparse(url).netloc
    )

    return metadata


def extract_metadata(url, timeout=10):
    """Fetch ``url`` and extract Twitter and OpenGraph metadata.

    Args:
        url (str): The URL to extract metadata from.
        timeout (int): Request timeout in seconds.

    Returns:
        dict: Metadata from :func:`parse_metadata`, or ``{'error': ..., 'url': ...}``
        if the request or parsing fails.
    """
    try:
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=timeout
        )
        response.raise_for_status()

        return parse_metadata(response.content, url)

    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "url": url}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}", "url": url}


def _utcnow_iso():
    """Return the current UTC time as an Atom-friendly ISO 8601 string."""
    return datetime.now().replace(microsecond=0).isoformat() + "Z"


def enrich_atom_entry(metadata, base_entry=None):
    """Create or enrich an Atom ``<entry>`` element from extracted metadata.

    Args:
        metadata (dict): Metadata from :func:`extract_metadata`.
        base_entry (Element, optional): Existing entry to enrich.

    Returns:
        Element: The Atom entry element.
    """
    if base_entry is None:
        entry = Element("entry")
    else:
        entry = base_entry

    # Title
    if metadata.get("title"):
        title_elem = entry.find("title")
        if title_elem is None:
            title_elem = SubElement(entry, "title")
        title_elem.text = metadata["title"]
        title_elem.set("type", "text")

    # Summary/Description
    if metadata.get("description"):
        summary_elem = entry.find("summary")
        if summary_elem is None:
            summary_elem = SubElement(entry, "summary")
        summary_elem.text = metadata["description"]
        summary_elem.set("type", "text")

    # Link to original content
    if metadata.get("url"):
        link_elem = SubElement(entry, "link")
        link_elem.set("rel", "alternate")
        link_elem.set("type", "text/html")
        link_elem.set("href", metadata["url"])

    # Image as enclosure
    if metadata.get("image"):
        enclosure_elem = SubElement(entry, "link")
        enclosure_elem.set("rel", "enclosure")
        # TODO: detect the actual image type instead of assuming JPEG.
        enclosure_elem.set("type", "image/jpeg")
        enclosure_elem.set("href", metadata["image"])

    # Content type as category
    og_type = metadata.get("opengraph", {}).get("type")
    if og_type:
        category_elem = SubElement(entry, "category")
        category_elem.set("term", og_type)
        category_elem.set("scheme", "http://ogp.me/ns#")

    # Published date (from article metadata)
    published_time = metadata.get("opengraph", {}).get("article:published_time")
    if published_time:
        try:
            pub_date = dateutil.parser.parse(published_time)
            published_elem = SubElement(entry, "published")
            published_elem.text = pub_date.isoformat()
        except Exception:
            pass

    # Updated date
    modified_time = metadata.get("opengraph", {}).get("article:modified_time")
    if modified_time:
        try:
            mod_date = dateutil.parser.parse(modified_time)
            updated_elem = entry.find("updated")
            if updated_elem is None:
                updated_elem = SubElement(entry, "updated")
            updated_elem.text = mod_date.isoformat()
        except Exception:
            pass

    # Author (from article metadata)
    author_name = metadata.get("opengraph", {}).get("article:author")
    twitter_creator = metadata.get("twitter", {}).get("creator")

    # Always add author element (required by Atom spec)
    author_elem = SubElement(entry, "author")
    SubElement(author_elem, "name").text = (
        author_name or twitter_creator or metadata.get("site_name", "Unknown")
    )

    # Site name as source - properly structured according to Atom spec
    if metadata.get("site_name"):
        source_elem = SubElement(entry, "source")
        # URI is required
        if metadata.get("url"):
            source_link = SubElement(source_elem, "link")
            source_link.set("rel", "alternate")
            source_link.set("type", "text/html")
            source_link.set("href", metadata["url"])

        # Required sub-elements for source
        source_title = SubElement(source_elem, "title")
        source_title.text = metadata["site_name"]

        source_id = SubElement(source_elem, "id")
        source_id.text = "urn:source:" + urlparse(metadata.get("url", "")).netloc

        source_updated = SubElement(source_elem, "updated")
        source_updated.text = _utcnow_iso()

    return entry


def enrich_url_list_to_atom(urls, feed_title=DEFAULT_FEED_TITLE, timeout=10):
    """Convert a list of URLs into an enriched Atom feed element.

    Args:
        urls (Iterable[str]): URLs to fetch and enrich.
        feed_title (str): The feed's ``<title>``.
        timeout (int): Per-request timeout in seconds.

    Returns:
        Element: The Atom ``<feed>`` root element.
    """
    # Create feed root
    feed = Element("feed")
    feed.set("xmlns", ATOM_NS)

    # Feed metadata
    SubElement(feed, "title").text = feed_title
    # Generate a unique UUID for the feed
    SubElement(feed, "id").text = "urn:uuid:" + str(uuid.uuid4())
    SubElement(feed, "updated").text = _utcnow_iso()

    # Add required self link (required by validators)
    self_link = SubElement(feed, "link")
    self_link.set("rel", "self")
    self_link.set("type", "application/atom+xml")
    self_link.set("href", "file:///enriched_feed.atom")

    for url in urls:
        metadata = extract_metadata(url, timeout=timeout)
        if "error" in metadata:
            logger.warning("Skipping %s: %s", url, metadata["error"])
            continue

        entry = enrich_atom_entry(metadata)
        # Add required ID and updated if missing
        if entry.find("id") is None:
            id_elem = SubElement(entry, "id")
            id_elem.text = url.strip()  # Ensure no whitespace
        if entry.find("updated") is None:
            updated_elem = SubElement(entry, "updated")
            updated_elem.text = _utcnow_iso()

        feed.append(entry)

    return feed


def fetch_sitemap_urls(sitemap_url, timeout=10):
    """Fetch a sitemap and return the list of ``<loc>`` URLs it contains.

    Args:
        sitemap_url (str): URL of the XML sitemap.
        timeout (int): Request timeout in seconds.

    Returns:
        list[str]: The URLs found in the sitemap.
    """
    logger.info("Fetching sitemap: %s", sitemap_url)
    response = requests.get(
        sitemap_url, timeout=timeout, headers={"User-Agent": USER_AGENT}
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "xml")
    urls = [loc.text for loc in soup.find_all("loc")]
    logger.info("Found %d URLs in the sitemap.", len(urls))
    return urls


def feed_to_pretty_xml(feed):
    """Serialise an Atom feed element to a pretty-printed XML string.

    Args:
        feed (Element): The Atom feed element.

    Returns:
        str: Indented, UTF-8 XML with blank lines collapsed.
    """
    rough_string = tostring(feed, encoding="utf-8")
    pretty = minidom.parseString(rough_string)
    formatted = pretty.toprettyxml(indent="    ", encoding="utf-8").decode("utf-8")
    # Remove the extra blank lines minidom adds
    return "\n".join(line for line in formatted.split("\n") if line.strip())
