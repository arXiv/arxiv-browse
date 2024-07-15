def test_no_source(client_with_test_fs, mocker):
    resp = client_with_test_fs.get("/pdf/1208.9998")
    assert resp.status_code == 404
    assert "1208.9998" in resp.text
    assert resp.headers.get('Expires', None) or resp.headers.get('Surrogate-Control', None)

    resp = client_with_test_fs.get("/pdf/1208.9998v1")
    assert resp.status_code == 404
    assert "1208.9998v1" in resp.text
    assert "max-age=31536000" in resp.headers.get('Surrogate-Control', None)

    resp = client_with_test_fs.get("/pdf/1208.9998v2")
    assert resp.status_code == 404
    assert "1208.9998v2" in resp.text
    assert resp.headers.get('Surrogate-Control', None)
