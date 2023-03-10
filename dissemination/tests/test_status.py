def test_status(client):
    resp = client.get("/pdf/status")
    assert resp.status_code == 200
    assert 'good' in resp.text
