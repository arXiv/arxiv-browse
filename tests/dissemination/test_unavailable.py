
def test_unavailable(client_with_test_fs):
    """Tests when there is no dissemination file for an existing tex version"""
    resp = client_with_test_fs.get("/pdf/1208.9999")
    assert resp.status_code == 500
    assert 'file unavailable' in resp.text
    headers= resp.headers
    assert  "max-age=31536000" in resp.headers.get("Surrogate-Control")    
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "unavailable-1208.9999-current", "paper-id-1208.9999", "paper-id-1208.9999-current"]
    assert all(" "+item+" " in keys for item in expected_keys)
    

    resp = client_with_test_fs.get("/pdf/1208.9999v1")
    assert resp.status_code == 500
    assert 'file unavailable' in resp.text
    headers= resp.headers
    assert  "max-age=31536000" in resp.headers.get("Surrogate-Control")
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "unavailable-1208.9999v1", "paper-id-1208.9999", "paper-id-1208.9999v1"]
    assert all(" "+item+" " in keys for item in expected_keys)

    resp = client_with_test_fs.get("/pdf/1208.9999v3")
    assert resp.status_code == 404
    headers= resp.headers
    assert  "max-age=31536000" in resp.headers.get("Surrogate-Control")
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "paper-id-1208.9999","unavailable-1208.9999v3", "paper-id-1208.9999v3"]
    assert all(" "+item+" " in keys for item in expected_keys)
