"""Test utility functions for generating response headers."""
from unittest import TestCase
from datetime import datetime
from dateutil.tz import tzutc


from browse.services.util.response_header import guess_next_update, mime_header_date
from browse.services.document.metadata import ARXIV_BUSINESS_TZ


class TestResponseHeaderUtils(TestCase):
    """Test response header utility functions."""

    def test_guess_next_update(self) -> None:
        """Test the guess_next_update function."""
        dt = datetime(year=2018, month=9, day=11, hour=19, minute=0, tzinfo=tzutc())
        next_publish_dt = guess_next_update(dt)
        expected_publish_dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tzutc())
        self.assertEquals(next_publish_dt, expected_publish_dt)

        dt = datetime(year=2018, month=9, day=14, hour=20, minute=1, tzinfo=tzutc())
        next_publish_dt = guess_next_update(dt)
        expected_publish_dt = datetime(year=2018, month=9, day=16, hour=20, minute=0, tzinfo=tzutc())
        self.assertEquals(next_publish_dt, expected_publish_dt)

    def test_mime_header_date(self) -> None:
        """Test MIME header date string is correct."""
        dt = datetime(year=2018, month=9, day=14, hour=20, minute=1, tzinfo=tzutc())
        self.assertEqual(mime_header_date(dt), 'Fri, 14 Sep 2018 20:01:00 GMT')
