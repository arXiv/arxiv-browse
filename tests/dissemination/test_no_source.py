def test_no_source(client_with_test_fs, mocker):
    resp = client_with_test_fs.get("/pdf/1208.9998.pdf")
    assert resp.status_code == 500
    assert "1208.9998" in resp.text
    assert resp.headers.get('Cache-Control', None) == "max-age=3000"

    resp = client_with_test_fs.get("/pdf/1208.9998v1.pdf")
    assert resp.status_code == 500
    assert "1208.9998v1" in resp.text
    assert resp.headers.get('Cache-Control', None) == "max-age=3000"

    resp = client_with_test_fs.get("/pdf/1208.9998v2.pdf")
    assert resp.status_code == 404
    assert "1208.9998v2" in resp.text
    assert resp.headers.get('Cache-Control', None) is None
    assert resp.headers.get('Expires', None) is not None
