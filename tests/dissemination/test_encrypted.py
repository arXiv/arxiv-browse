
def test_unavailable(client_with_test_fs):
    """Tests when there is no dissemination file for an existing tex version"""
    resp = client_with_test_fs.get("/src/0704.0380")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text

    resp = client_with_test_fs.get("/src/0704.0945v2")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text

    resp = client_with_test_fs.get("/src/0704.0945v3")
    assert resp.status_code == 404
