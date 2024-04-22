import pytest

def test_basic_lists(client_with_fake_listings):
    rv = client_with_fake_listings.get('/list/hep-ph/0901')
    assert rv.status_code == 200


def test_listing_expires_headers(client_with_fake_listings):
    rv = client_with_fake_listings.get('/list/hep-ph/0901')
    assert rv.status_code == 200

    pytest.skip('expires is not yet implemented')

    assert rv.headers.get('Expires', None)
