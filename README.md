# sitemap2atom

A simple tool to convert a sitemap.xml file into an Atom feed - especially useful for sites that don't have a CMS or where the CMS doesn't support Atom feeds.

## Usage

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the script:
   ```bash
   python test.py
   ```
3. The script will generate an `enriched_sitemap.xml` file in the same directory.

Configure the `sitemap_url` variable in `test.py` to point to your sitemap.xml file.

This is a simple script and may not handle all edge cases. It is designed for basic use cases where you have a sitemap.xml file and want to convert it to an Atom feed.
It does not support advanced features like authentication, pagination, or dynamic sitemaps, and may not work with all sitemap formats.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

PS. If you do anything interesting with this code, please let me know! I'd love to hear about it.
