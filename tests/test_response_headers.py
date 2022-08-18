"""Test utility functions for generating response headers."""
from datetime import datetime, timedelta
from unittest import TestCase

from arxiv.base.globals import get_application_config
from dateutil.tz import gettz, tzutc

from browse.services.util.response_headers import (
    APPROX_PUBLISH_DURATION,
    guess_next_update_utc,
    mime_header_date,
)


class TestResponseHeaderUtils(TestCase):
    """Test response header utility functions."""

    def test_guess_next_update_utc(self) -> None:
        """Test the guess_next_update_utc function."""

        config = get_application_config()
        tz = gettz('US/Eastern')

        dt = datetime(year=2018, month=9, day=11,
                      hour=19, minute=59, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=12, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=1, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tz)
        dt = dt + APPROX_PUBLISH_DURATION - timedelta(seconds=1)
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tz)
        dt = dt + APPROX_PUBLISH_DURATION
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=13,
                      hour=19, minute=59, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=14, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=13, hour=20, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=13, hour=20, minute=1, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=14, hour=15, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=15, hour=15, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=16, hour=16, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=16, hour=20, minute=5, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=18, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=16, hour=20, minute=5, tzinfo=tz)
        dt = dt + APPROX_PUBLISH_DURATION
        expected_publish_dt = datetime(
            year=2018, month=9, day=18, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(dt),
                              (expected_publish_dt, False))

    def test_mime_header_date(self) -> None:
        """Test MIME header date string is correct."""

        config = get_application_config()
        tz = gettz('US/Eastern')

        dt = datetime(year=2018, month=9, day=14,
                      hour=19, minute=1, tzinfo=tzutc())
        self.assertEqual(mime_header_date(dt), 'Fri, 14 Sep 2018 19:01:00 GMT')

        dt = datetime(year=2018, month=9, day=14,
                      hour=20, minute=1, tzinfo=tz)
        self.assertEqual(mime_header_date(dt), 'Sat, 15 Sep 2018 00:01:00 GMT')
