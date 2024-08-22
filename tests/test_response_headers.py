"""Test utility functions for generating response headers."""
from datetime import datetime, timedelta
from unittest import TestCase
from dateutil.tz import gettz, tzutc

from browse.controllers.response_headers import guess_next_update_utc, \
    mime_header_date, APPROX_PUBLISH_DURATION
from browse.controllers.response_headers import (
    APPROX_PUBLISH_DURATION,
    guess_next_update_utc,
    mime_header_date,
)


class TestResponseHeaderUtils(TestCase):
    """Test response header utility functions."""

    def test_guess_next_update_utc(self) -> None:
        """Test the guess_next_update_utc function."""
        tz = gettz('US/Eastern')

        dt = datetime(year=2018, month=9, day=11,
                      hour=19, minute=59, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=12, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=1, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tz)
        dt = dt + APPROX_PUBLISH_DURATION - timedelta(seconds=1)
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=11, hour=20, minute=0, tzinfo=tz)
        dt = dt + APPROX_PUBLISH_DURATION
        expected_publish_dt = datetime(
            year=2018, month=9, day=13, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=13,
                      hour=19, minute=59, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=14, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=13, hour=20, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=13, hour=20, minute=1, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=14, hour=15, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=15, hour=15, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=16, hour=16, minute=0, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=17, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

        dt = datetime(year=2018, month=9, day=16, hour=20, minute=5, tzinfo=tz)
        expected_publish_dt = datetime(
            year=2018, month=9, day=18, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, True))

        dt = datetime(year=2018, month=9, day=16, hour=20, minute=5, tzinfo=tz)
        dt = dt + APPROX_PUBLISH_DURATION
        expected_publish_dt = datetime(
            year=2018, month=9, day=18, hour=0, minute=0, tzinfo=tzutc())
        self.assertTupleEqual(guess_next_update_utc(tz, dt),
                              (expected_publish_dt, False))

    def test_mime_header_date(self) -> None:
        """Test MIME header date string is correct."""
        tz = gettz('US/Eastern')

        dt = datetime(year=2018, month=9, day=14,
                      hour=19, minute=1, tzinfo=tzutc())
        self.assertEqual(mime_header_date(dt), 'Fri, 14 Sep 2018 19:01:00 GMT')

        dt = datetime(year=2018, month=9, day=14,
                      hour=20, minute=1, tzinfo=tz)
        self.assertEqual(mime_header_date(dt), 'Sat, 15 Sep 2018 00:01:00 GMT')

#Tests for content of response headers

def test_content_type_header( client_with_test_fs) -> None:
    client=client_with_test_fs

    # single file native html
    resp = client.head("/html/2403.10561")
    assert resp.headers.get('Content-Type', '')== "text/html; charset=utf-8"

    #multifile native html
    resp = client.head("/html/cs/9901011")
    assert resp.headers.get('Content-Type', '')== "text/html; charset=utf-8"

    resp = client.head("/html/cs/9904010") #this one has multiple html files
    assert resp.headers.get('Content-Type', '')== "text/html; charset=utf-8"
    resp = client.head("/html/cs/9904010/report.htm")
    assert resp.headers.get('Content-Type', '')== "text/html; charset=utf-8"
    resp = client.head("/html/cs/9904010/graph4.gif")
    assert resp.headers.get('Content-Type', '')== "image/gif"
        
    #pdf path
    resp = client.head("/pdf/cs/0012007")
    assert resp.headers.get('Content-Type', '')== "application/pdf"

    #source in .gz
    resp = client.head("/e-print/cs/0011004")
    assert resp.headers.get('Content-Type', '')== "application/gzip"

    #source in tar.gz
    resp = client.head("/e-print/cs/0012007")
    assert resp.headers.get('Content-Type', '')== "application/gzip"
    resp = client.head("/pdf/cs/0012007")
    assert resp.headers.get('Content-Type', '')== "application/pdf"

    #source is pdf
    resp = client.head("/e-print/cs/0212040")
    assert resp.headers.get('Content-Type', '')== "application/pdf"

    #source file comes in a gz
    resp = client.head("/e-print/cond-mat/9805021v1")
    assert resp.headers.get('Content-Type', '')== "application/gzip"
