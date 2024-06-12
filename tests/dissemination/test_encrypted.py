
def test_no_src_access(client_with_test_fs):
    """Tests when there is no dissemination file for an existing tex version"""
    resp = client_with_test_fs.get("/src/0704.0380")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text

    resp = client_with_test_fs.get("/src/0704.0945v2")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text

    resp = client_with_test_fs.get("/e-print/0704.0945v2")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text

    resp = client_with_test_fs.get("/src/0704.0945v3")
    assert resp.status_code == 404

def test_still_read_article(client_with_test_fs):
    resp = client_with_test_fs.get("/html/0704.0380")
    assert resp.status_code != 403
    assert 'Source Not Public' not in resp.text

    resp = client_with_test_fs.get("/pdf/0704.0380")
    assert resp.status_code != 403
    assert 'Source Not Public' not in resp.text