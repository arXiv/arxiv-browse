"""Tests exception handling in :mod:`arxiv.base.exceptions`."""
import pytest
from http import HTTPStatus as status

from browse.services.documents.base_documents import AbsException
from browse.services.documents.config.deleted_papers import DELETED_PAPERS

@pytest.fixture()
def no_werkzeug_log():
    """Disable logging to avoid messy output during testing"""
    import logging
    wlog = logging.getLogger('werkzeug')
    wlog.disabled = True


def test_404(client_with_fake_listings, no_werkzeug_log):
    """A 404 response should be returned."""
    client = client_with_fake_listings
    for path in ('/foo', '/abs', '/abs/'):
        response = client.get(path)
        assert response.status_code == status.NOT_FOUND
        assert 'text/html' in  response.content_type

def test_404_unknown_version(client_with_fake_listings, no_werkzeug_log):
    response = client_with_fake_listings.get('/abs/1307.0001v999')
    assert response.status_code == status.NOT_FOUND

def test_404_oldstyle_nonexistant(client_with_fake_listings, no_werkzeug_log):
    """should get 404 for valid old paper ID with nonexistent paper number affix"""
    response = client_with_fake_listings.get('/abs/alg-geom/07059999')
    assert response.status_code == status.NOT_FOUND

def test_410_deleted_paper(client_with_fake_listings, no_werkzeug_log):
    'should get 410 for known deleted paper'
    response = client_with_fake_listings.get('/abs/astro-ph/0110242')
    assert response.status_code == status.GONE \
        and b'was a duplicate of astro-ph/0110255' in response.data

def test_410_deleted_paper_no_reason(client_with_fake_listings, no_werkzeug_log):
    'should get 410 for known deleted paper and no reason message'
    DELETED_PAPERS["astro-ph/9311999"] = ""
    response = client_with_fake_listings.get('/abs/astro-ph/9311999')
    assert response.status_code == status.GONE \
        and b'The reason recorded is' not in response.data

def test_404_bad_id(client_with_fake_listings, no_werkzeug_log):
    response = client_with_fake_listings.get('/abs/foo-bar/11223344')
    assert response.status_code == status.NOT_FOUND

def test_500(client_with_fake_listings, mocker ,no_werkzeug_log):
    """A 500 response should be returned."""
    abs = mocker.patch('browse.controllers.abs_page.get_abs_page')
    abs.side_effect = AbsException

    """Disable logging to avoid messy output during testing"""
    client_with_fake_listings.application.logger.disabled = True

    with pytest.raises(AbsException):
        response = client_with_fake_listings.get('/abs/1234.5678')
        assert response.status_code == status.INTERNAL_SERVER_ERROR
        assert 'text/html' in response.content_type
