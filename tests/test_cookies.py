"""test cookies"""



def test_cookies_with_no_params(client_with_test_fs):
    """Test the cookies page."""
    rv = client_with_test_fs.get('/cookies')
    assert rv.status_code == 200
    html = rv.data.decode('utf-8')
    assert 'Select preferred download format' in html
    assert 'show additional debugging information' in html, 'should have SHOW debugging link'

def test_cookies_with_debug(client_with_test_fs):
    """Test the cookies page."""
    rv = client_with_test_fs.get('/cookies?debug=1')
    assert rv.status_code == 200
    html = rv.data.decode('utf-8')
    assert 'Select preferred download format' in html
    assert 'hide debugging information' in html, 'should have HIDE debugging link'

def test_post_to_cookies(client_with_test_fs):
    rv = client_with_test_fs.post('/cookies/set?debug=1', data={'ps':'pdf'})
    assert rv.status_code == 302
    cookies =  map(lambda kv: kv[1], filter(lambda kv : kv[0]=='Set-Cookie', rv.headers.items()))
    assert 'xxx-ps-defaults=pdf; Path=/' in cookies
