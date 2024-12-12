"""test cookies"""


def test_cookies_with_no_params(client_with_test_fs):
    """Test the cookies page."""
    rv = client_with_test_fs.get('/cookies')
    assert rv.status_code == 200
    html = rv.data.decode('utf-8')
    assert 'show additional debugging information' in html, 'should have SHOW debugging link'

def test_cookies_with_debug(client_with_test_fs):
    """Test the cookies page."""
    rv = client_with_test_fs.get('/cookies?debug=1')
    assert rv.status_code == 200
    html = rv.data.decode('utf-8')
    assert 'hide debugging information' in html, 'should have HIDE debugging link'
