"""Tests for tb controllers, :mod:`browse.controllers.tb_page`."""

# mypy: ignore-errors
import pytest
from unittest import mock

from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest

from browse.controllers import tb_page
from browse.exceptions import TrackbackNotFound


@mock.patch('browse.controllers.tb_page.get_paper_trackback_pings')
def test_good_id_with_trackbacks(mock_get_paper_trackback_pings, app_with_test_fs) -> None:
    """Test requests with good arXiv identifiers known to the corpus."""
    with app_with_test_fs.app_context():
        mock_get_paper_trackback_pings.return_value = list()
        response_data, code, _ = tb_page.get_tb_page(arxiv_id='1901.05426')
        assert code == 200
        for key in ('arxiv_identifier', 'trackback_pings'):
            assert key in response_data, f"Response data should include '{key}'"

def test_bad_or_unknown_id(app_with_test_fs) -> None:
    """Test requests with bad arXiv identifiers."""
    with pytest.raises(TrackbackNotFound):
        for bad_or_unknown_id in ('foo', '1901.99999'):
            tb_page.get_tb_page(arxiv_id=bad_or_unknown_id)


@mock.patch('browse.controllers.tb_page.get_recent_trackback_pings')
def test_form_data(mock_get_recent_trackback_pings, app_with_test_fs) -> None:  # type: ignore
    """Test /tb/recent form data."""
    mock_get_recent_trackback_pings.return_value = list()

    form_data = MultiDict({
        'foo': 'bar'
    })
    with pytest.raises(BadRequest):
        tb_page.get_recent_tb_page(form_data)

    form_data = MultiDict({
        'views': 'baz'
    })
    with pytest.raises(BadRequest):
        tb_page.get_recent_tb_page(form_data)

    form_data = MultiDict({
        'views': '25'
    })
    response_data, code, headers = tb_page.get_recent_tb_page(form_data)
    assert code == 200
    assert 'max_trackbacks' in response_data, "Response data should include 'max_trackbacks'"
    assert response_data['max_trackbacks'] == 25, "'max_trackbacks' should equal value from form"
    assert 'recent_trackback_pings' in response_data, "Response data should include 'recent_trackback_pings'"
    assert 'article_map' in response_data, "Response data should include 'article_map'"


@mock.patch('browse.controllers.tb_page.get_trackback_ping')
def test_arguments(mock_trackback_ping, app_with_test_fs) -> None:  # type: ignore
    """Test /tb/redirect arguments."""
    with pytest.raises(TrackbackNotFound):
        # 'foo' is not an integer
        tb_page.get_tb_redirect(
            trackback_id='foo', hashed_document_id='feedface')

    with pytest.raises(TrackbackNotFound):
        # 'baz' is not a hex string
        tb_page.get_tb_redirect(
            trackback_id='1', hashed_document_id='baz')

    mtb = mock.Mock(
        trackback_id=1,
        hashed_document_id='feaedface',
        url='https://example.org'
    )
    mock_trackback_ping.return_value = mtb
    with pytest.raises(TrackbackNotFound):
        # parameters are OK, but hashed_document_id does not match
        _, code, headers = tb_page.get_tb_redirect(
            trackback_id='1', hashed_document_id='feedface')

    mtb = mock.Mock(
        trackback_id=2,
        hashed_document_id='f005ba11',
        url='https://example.com'
    )
    mock_trackback_ping.return_value = mtb

    _, code, headers = tb_page.get_tb_redirect(
        trackback_id='2', hashed_document_id='f005ba11')
    assert code == 301, 'Expect redirect for matching hashed_document_id'
    assert headers['Location'] == mtb.url, 'Redirect location header matches trackback URL'


def test_tb_bad_data(dbclient):
    resp = dbclient.get("/tb?uid=%27%22%20teste=efx-802&vid=%27%22%")
    assert resp.status_code == 400
