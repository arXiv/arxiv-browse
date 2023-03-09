from pathlib import Path

from browse.services.listing import ListingNew
from browse.services.listing.parse_new_listing_file import parse_new_listing_file

ASTRO_LISTS = "ftp/astro-ph/listings"

def test_parse_new(abs_path):
    parsed = parse_new_listing_file((abs_path / ASTRO_LISTS / "new"))
    assert isinstance(parsed, ListingNew)
    assert parsed
    assert parsed.listings
    assert parsed.expires
    assert parsed.new_count
    assert parsed.announced
    for item in parsed.listings:
        assert item and item.article
        assert item.listingType
        assert item.article.title
        if item.listingType in ['cross','new']:
            assert item.article.abstract
