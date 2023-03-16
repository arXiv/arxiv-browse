def test_status(client_with_test_fs):
    resp = client_with_test_fs.get("/pdf/status")
    assert resp.status_code == 200
    assert 'good' in resp.text
