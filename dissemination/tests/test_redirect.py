def test_redirect(client):
    resp = client.get("/pdf/cs/0212040v1")
    assert resp.status_code == 301

    resp = client.get("/pdf/1208.6335v1")
    assert resp.status_code == 301
