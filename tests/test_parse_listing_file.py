from pathlib import Path

from browse.services.listing import (
    NotModifiedResponse,
    get_listing_service,
    Listing,
    ListingNew,
)
from browse.services.listing.parse_listing_file import get_updates_from_list_file

ASTRO_LISTS = "ftp/astro-ph/listings"


def test_parse_month_lists(abs_path):
    for file in (abs_path / ASTRO_LISTS).glob("./[0-9]*"):
        yy = file.stem[0:2]
        mm = file.stem[2:4]
        parsed = get_updates_from_list_file(yy, mm, file, "month")
        assert isinstance(parsed, Listing)
        assert parsed
        assert parsed.listings
        assert parsed.count
        assert parsed.expires


def test_parse_new(abs_path):
    parsed = get_updates_from_list_file(0, 0, (abs_path / ASTRO_LISTS / "new"), "new")
    assert isinstance(parsed, ListingNew)
    assert parsed
    assert parsed.listings
    assert parsed.expires
    assert parsed.new_count
    assert parsed.announced
    assert parsed.listings[0].article
    assert parsed.listings[0].article.title
    assert parsed.listings[0].article.abstract

def test_parse_pastweek(abs_path):
    for file in (abs_path/ASTRO_LISTS).glob("pastweek.*"):
        parsed = get_updates_from_list_file(0, 0, file, "pastweek")
        assert isinstance(parsed, Listing)
        assert parsed
        assert parsed.listings
        assert parsed.count
        assert parsed.expires
