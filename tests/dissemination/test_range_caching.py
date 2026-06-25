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
import io
from datetime import datetime, timezone

import pytest

from arxiv.files import FileObj, LocalFileObj, MockStringFileObj, FileTransform
from arxiv.identifier import Identifier

from browse.controllers.files.dissemination import default_resp_fn

# A small PDF that exists in the test fixture filesystem (see test_response_headers).
PDF_PATH = "/pdf/cs/0012007"


def _make_sparse_pdf(path, size):
    """Create a `size`-byte PDF-ish file at `path` without writing `size` bytes.

    Uses a sparse file (seek past the end) so a ~20MB fixture is cheap to make.
    """
    with open(path, "wb") as fh:
        fh.write(b"%PDF-1.4\n")
        fh.seek(size - 1)
        fh.write(b"\0")
    assert path.stat().st_size == size
    return path


def test_caching_setup_default(client_with_test_fs):
    """The whole-object cache threshold defaults to Fastly's 20 MB limit."""
    assert client_with_test_fs.application.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] \
        == 20 * 1024 * 1024


def test_small_object_range_served_whole_and_cacheable(client_with_test_fs):
    """A Range request for a sub-threshold object is answered in full (200) and
    carries the headers Fastly needs to cache the WHOLE object."""
    resp = client_with_test_fs.get(PDF_PATH, headers={"Range": "bytes=0-1"})
    assert resp.status_code == 200                       # served whole, not 206
    assert "Content-Range" not in resp.headers           # i.e. not a partial response
    assert resp.headers["Accept-Ranges"] == "bytes"      # still advertises range support
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")  # cacheable at Fastly
    assert resp.headers.get("ETag")                      # validator for the cached object
    assert resp.headers.get("Content-Type") == "application/pdf"
    # The whole object must be returned with a definite Content-Length and NOT
    # chunked. A length-less chunked 200 is not a cacheable whole object for
    # Fastly -- it stored only the first ~1MB -- which is the flaw this guards.
    assert resp.headers.get("Content-Length")
    assert int(resp.headers["Content-Length"]) == len(resp.data)
    assert "chunked" not in resp.headers.get("Transfer-Encoding", "").lower()
    # the body delivered is the full file, not a truncated prefix
    assert len(resp.data) == int(resp.headers["Content-Length"])


def test_no_range_is_full_200(client_with_test_fs):
    """A plain GET (no Range header) is unchanged: a full, cacheable 200."""
    resp = client_with_test_fs.get(PDF_PATH)
    assert resp.status_code == 200
    assert resp.headers["Accept-Ranges"] == "bytes"
    assert "Content-Range" not in resp.headers
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")
    # small object served whole with a definite length so Fastly caches all of it
    assert resp.headers.get("Content-Length")
    assert int(resp.headers["Content-Length"]) == len(resp.data)
    assert "chunked" not in resp.headers.get("Transfer-Encoding", "").lower()


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


def test_19_9MB_object_returned_whole_not_truncated(client_with_test_fs, tmp_path):
    """A 19.9 MB object -- just under the 20 MiB FASTLY_CACHE_MAX_OBJECT_SIZE --
    answered to a Range request must come back as a complete 200: the WHOLE body,
    a definite Content-Length, and no chunked encoding. This is the regression
    guard for the flaw where Fastly cached only the first ~1MB of such files.

    The fixture is generated at test time under pytest's tmp_path (never checked
    into git) and is removed in the finally block below.
    """
    size = int(19.9 * 1024 * 1024)  # 19.9 MiB, just under the 20 MiB threshold
    pdf = _make_sparse_pdf(tmp_path / "big.pdf", size)
    try:
        app = client_with_test_fs.application
        assert size < app.config["FASTLY_CACHE_MAX_OBJECT_SIZE"]
        file = LocalFileObj(pdf)
        with app.test_request_context(PDF_PATH, headers={"Range": "bytes=0-1"}):
            resp = default_resp_fn(file, Identifier("cs/0012007"))
            body = resp.get_data()
        assert resp.status_code == 200                 # whole object, not 206
        assert "Content-Range" not in resp.headers     # not a partial response
        assert resp.headers["Accept-Ranges"] == "bytes"
        assert "chunked" not in resp.headers.get("Transfer-Encoding", "").lower()
        assert int(resp.headers["Content-Length"]) == size  # advertises the whole size
        assert len(body) == size                       # the ENTIRE object is returned, not the first ~1MB
    finally:
        pdf.unlink(missing_ok=True)


def test_transformed_file_stays_chunked(client_with_test_fs):
    """A FileTransform produces its bytes on the fly and its .size is the source
    size, not the transformed length. Such responses must be streamed chunked
    (no Content-Length), or we would advertise a wrong length and truncate the
    body."""
    src = MockStringFileObj("paper.html", "<html>x</html>")
    # transform whose output length differs from the source length
    file = FileTransform(src, lambda data: data + b"-appended-by-transform")
    expected = b"<html>x</html>-appended-by-transform"

    app = client_with_test_fs.application
    with app.test_request_context("/html/2101.00001"):
        resp = default_resp_fn(file, Identifier("2101.00001"))
        body = resp.get_data()
    assert resp.status_code == 200
    assert "chunked" in resp.headers.get("Transfer-Encoding", "").lower()
    assert "Content-Length" not in resp.headers       # never advertise the lying source size
    assert body == expected                            # full transformed body delivered


def test_head_transformed_file_omits_content_length(client_with_test_fs):
    """HEAD for a FileTransform must NOT advertise a Content-Length.

    file.size is the source size (a lie) for transforms, and the GET for a
    transform is chunked with no Content-Length. HTTP requires HEAD to send the
    same headers GET would, so HEAD must omit Content-Length too -- otherwise a
    HEAD to /html/<id> reports the wrong (source) length to clients such as
    download managers.
    """
    src = MockStringFileObj("paper.html", "<html>x</html>")
    file = FileTransform(src, lambda data: data + b"-appended-by-transform")

    app = client_with_test_fs.application
    with app.test_request_context("/html/2101.00001", method="HEAD"):
        resp = default_resp_fn(file, Identifier("2101.00001"))
    assert "Content-Length" not in resp.headers       # don't report the lying source size on HEAD
    assert resp.headers["Accept-Ranges"] == "bytes"


def test_transform_with_range_is_not_partial_206(client_with_test_fs):
    """A transform answered to a Range request must never become a 206.

    A transform's .size is the source size (a lie), so a 206/Content-Range built
    from it describes a length the transformed body does not have -- Fastly would
    cache a corrupt partial. Even when the (lying) source size is over the 206
    threshold, a ranged transform must fall through to a chunked whole 200.
    """
    src = MockStringFileObj("paper.html", "<html>x</html>")
    file = FileTransform(src, lambda data: data + b"-appended-by-transform")
    expected = b"<html>x</html>-appended-by-transform"

    app = client_with_test_fs.application
    original = app.config.get("FASTLY_CACHE_MAX_OBJECT_SIZE")
    app.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] = 0  # push the (lying) source size over the threshold
    try:
        with app.test_request_context("/html/2101.00001", headers={"Range": "bytes=0-1"}):
            resp = default_resp_fn(file, Identifier("2101.00001"))
            body = resp.get_data()
        assert resp.status_code != 206                 # never a partial response for a transform
        assert "Content-Range" not in resp.headers
        assert "Content-Length" not in resp.headers    # never advertise the lying size
        assert "chunked" in resp.headers.get("Transfer-Encoding", "").lower()
        assert body == expected                        # full transformed body delivered
    finally:
        app.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] = original


def test_large_object_plain_get_is_chunked(client_with_test_fs, tmp_path):
    """A verbatim object over the threshold, plain GET (no Range), is streamed
    chunked with no Content-Length: Cloud Run cannot buffer the whole body and
    Fastly cannot whole-object cache something over its size limit anyway."""
    app = client_with_test_fs.application
    size = app.config["FASTLY_CACHE_MAX_OBJECT_SIZE"] + 1024  # just over the limit
    pdf = _make_sparse_pdf(tmp_path / "over.pdf", size)
    try:
        file = LocalFileObj(pdf)
        with app.test_request_context(PDF_PATH):       # plain GET, no Range header
            resp = default_resp_fn(file, Identifier("cs/0012007"))
        assert resp.status_code == 200
        assert "chunked" in resp.headers.get("Transfer-Encoding", "").lower()
        assert "Content-Length" not in resp.headers    # length-less chunked, as documented
        assert resp.headers["Accept-Ranges"] == "bytes"
    finally:
        resp.close()
        pdf.unlink(missing_ok=True)


class _LyingSizeFile(FileObj):
    """A verbatim-looking FileObj whose .size under-reports the real body.

    Simulates a size that lies (e.g. a gzip-on-read FileObj that reports its
    *compressed* length while open() yields the larger decompressed body). It is
    not a FileTransform, so the whole-200 path would set Content-Length=.size --
    the guard must refuse to stream a body that disagrees with that length.
    """

    def __init__(self, data: bytes, lied_size: int):
        self._data = data
        self._lied_size = lied_size

    @property
    def name(self) -> str:
        return "lying.pdf"

    def exists(self) -> bool:
        return True

    def open(self, mode: str = "rb") -> io.BytesIO:
        return io.BytesIO(self._data)

    @property
    def etag(self) -> str:
        return "lying-etag"

    @property
    def size(self) -> int:
        return self._lied_size

    @property
    def updated(self) -> datetime:
        return datetime(2020, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("lied_size, desc", [
    (100, "size under-reports the body (e.g. a compressed length)"),
    (5009 + 5000, "size over-reports the body (e.g. a truncated/short read)"),
])
def test_lying_size_never_serves_a_length_mismatched_200(
        client_with_test_fs, lied_size, desc):
    """The core guarantee: we never emit a 200 whose body length disagrees with
    its Content-Length, because Fastly would cache the mismatched bytes as a
    complete object. Whether the declared size is too small (we would otherwise
    overrun) or too large (the body falls short), the stream must abort rather
    than hand the edge a cacheable, corrupt object.
    """
    data = b"%PDF-1.4\n" + b"x" * 5000          # 5009-byte actual body
    file = _LyingSizeFile(data, lied_size=lied_size)

    app = client_with_test_fs.application
    with app.test_request_context(PDF_PATH):
        resp = default_resp_fn(file, Identifier("cs/0012007"))
        assert resp.headers.get("Content-Length") == str(lied_size)  # the (wrong) declared length
        # Consuming the body must raise instead of yielding a length-mismatched
        # 200 -- the edge never gets a cacheable, corrupt object.
        with pytest.raises(IOError):
            resp.get_data()
