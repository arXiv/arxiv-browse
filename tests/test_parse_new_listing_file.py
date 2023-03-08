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
    assert parsed.listings[0].article
    assert parsed.listings[0].article.title
    assert parsed.listings[0].article.abstract
