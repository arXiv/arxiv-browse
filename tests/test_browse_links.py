from bs4 import BeautifulSoup


def test_newer_id(client_with_test_fs):
    rv = client_with_test_fs.get('/abs/1604.08245')
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
    assert html is not None

    current_context = html.find('div', 'current')
    assert current_context is not None
    assert current_context.text == 'cs.MM'

    pn_div = html.find('div', 'prevnext')
    assert pn_div is not None, 'Should have div.prevnext'
    assert pn_div.find_all('span', 'arrow')[0].a['title'] == 'previous in cs.MM (accesskey p)', 'Should have previous span.arrow subtags with correct category'

    assert pn_div.find_all('span', 'arrow')[1].a['title'] == 'next in cs.MM (accesskey n)', 'Should have next span.arrow subtags with correct category'

    switches = html.find_all('div', 'switch')
    assert len(switches) ==  1, 'Should only be one context to switch to'
    assert switches[0].a.text == 'cs', 'switch context should be cs'

def test_older_id(client_with_test_fs):
    rv = client_with_test_fs.get('/abs/ao-sci/9503001')
    rv.status_code == 200
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
    assert html is not None

    current_context = html.find('div', 'current')
    assert current_context is not None
    assert current_context.text == 'ao-sci'

    pn_div = html.find('div', 'prevnext')
    assert pn_div, 'Should have div.prevnext'

    atags = pn_div.find_all('a')
    assert len(atags) >= 1, 'Shold be at least one <a> tags for prev/next'

    assert pn_div.find_all('a')[0]['title'] == 'previous in ao-sci (accesskey p)', 'Should have previous span.arrow subtags with correct category'

    switches = html.find_all('div', 'switch')
    assert len(switches) == 0, 'Should be no other contxt to switch to'

def test_older_id_w_canonical(client_with_test_fs):
    rv = client_with_test_fs.get('/abs/physics/9707012')
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
    assert html

    current_context = html.find('div', 'current')
    assert 'math-ph' in current_context

    pn_div = html.find('div', 'prevnext')
    assert pn_div, 'Should have div.prevnext'

    atags = pn_div.find_all('a')
    assert len(atags) >= 1, 'Shold be at least one <a> tags for prev/next'

    assert pn_div.find_all('a')[0]['title'] == 'previous in math-ph (accesskey p)', 'Should have previous span.arrow subtags with correct category'

    switches = html.find_all('div', 'switch')
    assert len(switches) == 0, 'Should be no other contxt to switch to'

    other_atags = html.find('div','list').find_all('a')
    assert other_atags
    assert len(other_atags) >= 3, "should be at least 3 a tags in list"
    assert other_atags[0]['href'] == '/list/math-ph/new'
    assert other_atags[1]['href'] == '/list/math-ph/recent'
    assert other_atags[2]['href'] == '/list/math-ph/9707'
