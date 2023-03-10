
def test_unavailable(client):
    """Tests when there is no PDF for an existing tex version"""
    resp = client.get("/pdf/1208.9999.pdf")
    assert resp.status_code == 500
    assert 'PDF unavailable' in resp.text

    resp = client.get("/pdf/1208.9999v1.pdf")
    assert resp.status_code == 500
    assert 'PDF unavailable' in resp.text

    resp = client.get("/pdf/1208.9999v3.pdf")
    assert resp.status_code == 404
