from pathlib import Path

from browse.services.listing import Listing
from browse.services.listing.parse_listing_file import get_updates_from_list_file

ASTRO_LISTS = "ftp/astro-ph/listings"


def test_parse_month_lists(abs_path):
    for file in (abs_path / ASTRO_LISTS).glob("./[0-9]*"):
        yy = file.stem[0:2]
        mm = file.stem[2:4]
        parsed = get_updates_from_list_file(yy, mm, file, "month")
        assert parsed and isinstance(parsed, Listing)
        assert parsed.listings
        assert parsed.count
        assert parsed.expires
