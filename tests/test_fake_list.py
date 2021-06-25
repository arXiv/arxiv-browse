
def test_basic_lists(client_with_fake_listings):
    rv = client_with_fake_listings.get('/list/hep-ph/0901')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None)
