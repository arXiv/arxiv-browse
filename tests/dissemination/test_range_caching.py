"""Tests for the Fastly range/caching behaviour of file dissemination.

Background: in-browser PDF viewers (and the CDN itself) issue HTTP Range
requests. If the origin answers every Range request with a 206 Partial Content,
Fastly will not cache the object, so each range request is forwarded to the
origin -- which on arxiv-production was the dominant driver of carrier-peering
egress cost.

The dissemination controller therefore only emits a 206 for objects larger than
``FASTLY_CACHE_MAX_OBJECT_SIZE`` (objects Fastly cannot cache whole and must
fetch via segmented caching). Smaller objects are returned in full (200) so
Fastly caches them once and synthesizes later range responses from the edge.
"""
import pytest

# A small PDF that exists in the test fixture filesystem (see test_response_headers).
PDF_PATH = "/pdf/cs/0012007"


def test_caching_setup_default(client_with_test_fs):
    """The whole-object cache threshold defaults to Fastly's 20 MB limit."""
    assert client_with_test_fs.application.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] \
        == 20 * 1024 * 1024


def test_small_object_range_served_whole_and_cacheable(client_with_test_fs):
    """A Range request for a sub-threshold object is answered in full (200) and
    carries the headers Fastly needs to cache it."""
    resp = client_with_test_fs.get(PDF_PATH, headers={"Range": "bytes=0-1"})
    assert resp.status_code == 200                       # served whole, not 206
    assert "Content-Range" not in resp.headers           # i.e. not a partial response
    assert resp.headers["Accept-Ranges"] == "bytes"      # still advertises range support
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")  # cacheable at Fastly
    assert resp.headers.get("ETag")                      # validator for the cached object
    assert resp.headers.get("Content-Type") == "application/pdf"


def test_no_range_is_full_200(client_with_test_fs):
    """A plain GET (no Range header) is unchanged: a full, chunked 200."""
    resp = client_with_test_fs.get(PDF_PATH)
    assert resp.status_code == 200
    assert resp.headers["Accept-Ranges"] == "bytes"
    assert "Content-Range" not in resp.headers
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")


def test_large_object_served_as_206_for_segmented_caching(client_with_test_fs):
    """An object above the threshold is served as 206 Partial Content so Fastly
    segmented caching can fetch it in range-sized pieces."""
    app = client_with_test_fs.application
    original = app.config.get("FASTLY_CACHE_MAX_OBJECT_SIZE")
    app.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] = 0  # force every object over the limit
    try:
        resp = client_with_test_fs.get(PDF_PATH, headers={"Range": "bytes=0-1"})
        assert resp.status_code == 206
        assert resp.headers.get("Content-Range", "").startswith("bytes 0-1/")
        # cache headers are still present so Fastly's segmented caching can store the pieces
        assert "max-age=31536000" in resp.headers.get("Surrogate-Control")
    finally:
        app.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] = original
