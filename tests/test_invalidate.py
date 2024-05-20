from typing import List, Optional

import pytest
from arxiv.identifier import Identifier
from pytest_mock import mocker
from browse.invalidator import Invalidator, _paperid, purge_urls
from browse.invalidator.app import create_app


@pytest.mark.parametrize("key, paperid", [
    ("ps_cache/arxiv/pdf/0701/0712.0830v1.pdf", "0712.0830v1"),
    ("ps_cache/arxiv/pdf/2401/2401.08337v2.pdf", "2401.08337v2"),
    ("arxiv-production-data/ps_cache/hep-ph/pdf/0511/0511005v2.pdf", "hep-ph/0511005v2"),
    ("arxiv-production-data/bogus", None),
    ("", None),
])
def test_paperid(key: str, paperid: Optional[str]) -> None:
    aid = _paperid(key)
    assert aid == paperid or aid and aid.idv == paperid


@pytest.mark.parametrize("key, urls", [
    ("ps_cache/arxiv/pdf/0701/0712.0830v1.pdf", ['arxiv.org/pdf/0712.0830v1', 'arxiv.org/pdf/0712.0830']),
    ("ps_cache/arxiv/pdf/0701/0712.0830v2.pdf", ['arxiv.org/pdf/0712.0830v2', 'arxiv.org/pdf/0712.0830']),
    ("ps_cache/arxiv/pdf/0701/0712.0830v11.pdf", ['arxiv.org/pdf/0712.0830v11', 'arxiv.org/pdf/0712.0830']),
    ("ps_cache/arxiv/ps/0701/0712.0830v11.ps", ['arxiv.org/ps/0712.0830v11', 'arxiv.org/ps/0712.0830']),
    ("ps_cache/arxiv/dvi/0701/0712.0830v11.dvi", ['arxiv.org/dvi/0712.0830v11', 'arxiv.org/dvi/0712.0830']),
    ("ps_cache/arxiv/html/0701/0712.0830v11.html.gz",
     ['arxiv.org/html/0712.0830v11', 'arxiv.org/html/0712.0830', 'arxiv.org/html/0712.0830v11/',
      'arxiv.org/html/0712.0830/']),
    ("arxiv-production-data/ps_cache/hep-ph/pdf/0511/0511005v2.pdf",
     ['arxiv.org/pdf/hep-ph/0511005v2', 'arxiv.org/pdf/hep-ph/0511005', ]),
    ("arxiv-production-data/bogus", None),
    ("", None),
])
def test_purge_urls(key: str, urls: List[str]) -> None:
    pp = purge_urls(key)
    assert pp == urls or pp is not None and pp[1] == urls


def test_invalidate(mocker):  # type: ignore
    get = mocker.patch('browse.invalidator.requests.get')
    get.return_value.status_code = 200
    inv = Invalidator("https://example.com", "FAKE_API_TOKEN_abc1234")
    inv.invalidate("fake_url", Identifier("1901.0001"))
    get.assert_called_once_with('https://example.com/fake_url', headers={'Fastly-Key': 'FAKE_API_TOKEN_abc1234'})


@pytest.fixture
def mocked_request_get(mocker):  # type: ignore
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    mocked_get = mocker.patch('browse.invalidator.requests.get')
    mocked_get.return_value = MockResponse(200)
    yield mocked_get


def test_invalidate_app(mocked_request_get):  # type: ignore
    xapp = create_app()
    xapp.config["FASTLY_API_TOKEN"] = "FAKE_API_TOKEN_abc1234"
    xapp.config["FASTLY_URL"] = "https://example.com/purge"

    with xapp.test_client() as app:
        resp = app.post("/", json={
            "kind": "storage#object",
            "id": "arxiv-production-data/txt/test/test.txt/1715976725972877",
            "name": "txt/test/test.txt",
            "bucket": "arxiv-production-data",
            "generation": "1715976725972877",
            "metageneration": "1",
            "contentType": "text/plain",
            "timeCreated": "2024-05-17T20:12:06.024Z",
            "updated": "2024-05-17T20:12:06.024Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-05-17T20:12:06.024Z",
            "size": "56",
            "md5Hash": "c6Ey9je4h4MN/kI6ONZRYw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/arxiv-production-data/o/txt%2Ftest%2Ftest.txt?generation=1715976725972877&alt=media",
            "contentLanguage": "en",
            "crc32c": "boLwHQ==",
            "etag": "CI2Px7m/lYYDEAE="
        },
                        content_type='application/json'
                        )
        assert resp and resp.status_code == 200
        assert mocked_request_get.call_count == 0

        resp = app.post("/", json={
                "name": "ps_cache/arxiv/pdf/0701/0712.0830v1.pdf",
                "bucket": "arxiv-production-data",
            },
            content_type='application/json')

        assert resp and resp.status_code == 200
        assert mocked_request_get.call_count == 2

        all_calls = mocked_request_get.call_args_list
        assert all_calls[0][0] == ('https://example.com/purge/arxiv.org/pdf/0712.0830v1',)
        assert all_calls[0][1] == {'headers': {'Fastly-Key': 'FAKE_API_TOKEN_abc1234'}}
        assert all_calls[1][0] == ('https://example.com/purge/arxiv.org/pdf/0712.0830',)
        assert all_calls[1][1] == {'headers': {'Fastly-Key': 'FAKE_API_TOKEN_abc1234'}}
