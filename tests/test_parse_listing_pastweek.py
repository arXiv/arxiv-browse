from browse.services.listing import ListingPastweek

from browse.services.listing.parse_listing_pastweek import parse_listing_pastweek

ASTRO_LISTS = "ftp/astro-ph/listings"

def test_parse_pastweek(abs_path):
    for file in (abs_path/ASTRO_LISTS).glob("pastweek.*"):
        parsed = parse_listing_pastweek(file)
        assert parsed and isinstance(parsed, ListingPastweek), f"problem with {file}"
        assert parsed.listings
        assert parsed.count
        assert parsed.expires
