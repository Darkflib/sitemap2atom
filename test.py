import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
import dateutil.parser
import logging
import uuid

def extract_metadata(url, timeout=10):
    """
    Extract Twitter and OpenGraph metadata from a URL.
    
    Args:
        url (str): The URL to extract metadata from
        timeout (int): Request timeout in seconds
        
    Returns:
        dict: Dictionary containing extracted metadata
    """
    try:
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        metadata = {
            'url': url,
            'title': None,
            'description': None,
            'image': None,
            'site_name': None,
            'twitter': {},
            'opengraph': {}
        }
        
        # Extract OpenGraph metadata
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        for tag in og_tags:
            prop = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if prop and content:
                metadata['opengraph'][prop] = content
                
        # Extract Twitter metadata
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        for tag in twitter_tags:
            name = tag.get('name', '').replace('twitter:', '')
            content = tag.get('content', '')
            if name and content:
                metadata['twitter'][name] = content
                
        # Populate main fields from OG or Twitter data
        metadata['title'] = (
            metadata['opengraph'].get('title') or 
            metadata['twitter'].get('title') or
            (soup.find('title').get_text().strip() if soup.find('title') else None)
        )
        
        metadata['description'] = (
            metadata['opengraph'].get('description') or 
            metadata['twitter'].get('description') or
            (soup.find('meta', attrs={'name': 'description'}) or {}).get('content')
        )
        
        # Handle image URLs (make absolute if relative)
        image_url = (
            metadata['opengraph'].get('image') or 
            metadata['twitter'].get('image')
        )
        if image_url:
            metadata['image'] = urljoin(url, image_url)
            
        metadata['site_name'] = (
            metadata['opengraph'].get('site_name') or
            metadata['twitter'].get('site') or
            urlparse(url).netloc
        )
        
        return metadata
        
    except requests.RequestException as e:
        return {'error': f'Request failed: {str(e)}', 'url': url}
    except Exception as e:
        return {'error': f'Parsing failed: {str(e)}', 'url': url}

def enrich_atom_entry(metadata, base_entry=None):
    """
    Create or enrich an Atom entry element with extracted metadata.
    
    Args:
        metadata (dict): Metadata from extract_metadata()
        base_entry (Element, optional): Existing entry to enrich
        
    Returns:
        Element: Atom entry element
    """
    if base_entry is None:
        entry = Element('entry')
    else:
        entry = base_entry
    
    # Title
    if metadata.get('title'):
        title_elem = entry.find('title')
        if title_elem is None:
            title_elem = SubElement(entry, 'title')
        title_elem.text = metadata['title']
        title_elem.set('type', 'text')
    
    # Summary/Description
    if metadata.get('description'):
        summary_elem = entry.find('summary')
        if summary_elem is None:
            summary_elem = SubElement(entry, 'summary')
        summary_elem.text = metadata['description']
        summary_elem.set('type', 'text')
    
    # Link to original content
    if metadata.get('url'):
        link_elem = SubElement(entry, 'link')
        link_elem.set('rel', 'alternate')
        link_elem.set('type', 'text/html')
        link_elem.set('href', metadata['url'])
    
    # Image as enclosure
    if metadata.get('image'):
        enclosure_elem = SubElement(entry, 'link')
        enclosure_elem.set('rel', 'enclosure')
        enclosure_elem.set('type', 'image/jpeg')  # You might want to detect actual type
        enclosure_elem.set('href', metadata['image'])
    
    # Content type as category
    og_type = metadata.get('opengraph', {}).get('type')
    if og_type:
        category_elem = SubElement(entry, 'category')
        category_elem.set('term', og_type)
        category_elem.set('scheme', 'http://ogp.me/ns#')
    # Published date (from article metadata)
    published_time = metadata.get('opengraph', {}).get('article:published_time')
    if published_time:
        try:
            pub_date = dateutil.parser.parse(published_time)
            published_elem = SubElement(entry, 'published')
            published_elem.text = pub_date.isoformat()
        except Exception:
            pass
    # Updated date
    modified_time = metadata.get('opengraph', {}).get('article:modified_time')
    if modified_time:
        try:
            mod_date = dateutil.parser.parse(modified_time)
            updated_elem = entry.find('updated')
            if updated_elem is None:
                updated_elem = SubElement(entry, 'updated')
            updated_elem.text = mod_date.isoformat()
        except Exception:
            pass    # Author (from article metadata)
    author_name = metadata.get('opengraph', {}).get('article:author')
    twitter_creator = metadata.get('twitter', {}).get('creator')
    
    # Always add author element (required by Atom spec)
    author_elem = SubElement(entry, 'author')
    SubElement(author_elem, 'name').text = author_name or twitter_creator or metadata.get('site_name', 'Unknown')
    
    # Site name as source - properly structured according to Atom spec
    if metadata.get('site_name'):
        source_elem = SubElement(entry, 'source')
        # URI is required
        if metadata.get('url'):
            source_link = SubElement(source_elem, 'link')
            source_link.set('rel', 'alternate')
            source_link.set('type', 'text/html')
            source_link.set('href', metadata['url'])
            
        # Required sub-elements for source
        source_title = SubElement(source_elem, 'title')
        source_title.text = metadata['site_name']
        
        source_id = SubElement(source_elem, 'id')
        source_id.text = 'urn:source:' + urlparse(metadata.get('url', '')).netloc
        
        source_updated = SubElement(source_elem, 'updated')
        source_updated.text = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    
    return entry

# Usage example for enriching a feed
def enrich_url_list_to_atom(urls):
    """Convert a list of URLs to an enriched Atom feed"""
    from xml.etree.ElementTree import Element, SubElement
    
    # Create feed root
    feed = Element('feed')
    feed.set('xmlns', 'http://www.w3.org/2005/Atom')      # Feed metadata
    SubElement(feed, 'title').text = 'Enriched URL Feed'
    # Generate a unique UUID for the feed
    SubElement(feed, 'id').text = 'urn:uuid:' + str(uuid.uuid4())
    SubElement(feed, 'updated').text = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    
    # Add required self link (required by validators)
    self_link = SubElement(feed, 'link')
    self_link.set('rel', 'self')
    self_link.set('type', 'application/atom+xml')
    self_link.set('href', 'file:///enriched_feed.atom')
    
    for url in urls:
        metadata = extract_metadata(url)
        if 'error' not in metadata:
            entry = enrich_atom_entry(metadata)            # Add required ID and updated if missing
            if entry.find('id') is None:
                id_elem = SubElement(entry, 'id')
                id_elem.text = url.strip()  # Ensure no whitespace
            if entry.find('updated') is None:
                updated_elem = SubElement(entry, 'updated')
                updated_elem.text = datetime.now().replace(microsecond=0).isoformat() + 'Z'
                
            feed.append(entry)
    
    return feed

if __name__ == "__main__":
    # Example usage
    sitemap_url = f"https://www.thetimes.com/sitemaps/articles/{datetime.now().year}/{datetime.now().month:02d}/{datetime.now().day:02d}"  # Replace with your sitemap URL - the times sitemap uses a date-based structure with daily updates
    domain = sitemap_url.split('/')[2]  # Extract domain from URL
    logging.info(f"Domain extracted from sitemap URL: {domain}")
    logging.info(f"Starting Sitemap2Atom conversion for sitemap: {sitemap_url}")
    # Fetch URLs from the sitemap
    response = requests.get(sitemap_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'xml')
    urls = [url.text for url in soup.find_all('loc')]
    logging.info(f"Found {len(urls)} URLs in the sitemap.")
    
    # Chop the URLs to a manageable size for testing
    urls = urls[:10]  # Limit to first 10 URLs for testing
    
    # Enrich each URL   
    feed = enrich_url_list_to_atom(urls)    # Always format the output with pretty indentation and proper encoding
    from xml.dom import minidom
    import xml.etree.ElementTree as ET
    
    # Convert to string for output
    rough_string = ET.tostring(feed, encoding='utf-8')
    
    # Use minidom to format properly
    pretty_feed = minidom.parseString(rough_string)
    formatted_xml = pretty_feed.toprettyxml(indent="    ", encoding='utf-8').decode('utf-8')
    
    # Remove extra whitespace that minidom adds
    formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
    
    print(formatted_xml)

    # Save the enriched Atom feed to a file
    with open('enriched_feed.atom', 'w', encoding='utf-8') as f:
        f.write(formatted_xml)



# Example usage
#if __name__ == "__main__":
#    url = "https://example.com"
#    result = extract_metadata(url)
#    
#    if 'error' not in result:
#        print(f"Title: {result['title']}")
#        print(f"Description: {result['description']}")
#        print(f"Image: {result['image']}")
#        print(f"Site: {result['site_name']}")
#        print(f"OpenGraph tags: {len(result['opengraph'])}")
#        print(f"Twitter tags: {len(result['twitter'])}")
#    else:
#        print(f"Error: {result['error']}")

