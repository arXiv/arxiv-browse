
def test_no_src_access(client_with_test_fs):
    """Tests when there is no dissemination file for an existing tex version"""

    #current version of an encrypted file might change
    resp = client_with_test_fs.get("/src/0704.0380")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text
    headers= resp.headers
    assert headers["Surrogate-Control"]== "max-age=86400"
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable","unavailable-0704.0380-current", "paper-id-0704.0380", "not-public", "paper-id-0704.0380-current", "src"]
    assert all(" "+item+" " in keys for item in expected_keys)

    #specific version that isnt public will stay that way
    resp = client_with_test_fs.get("/src/0704.0945v2")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text
    headers= resp.headers
    assert headers["Surrogate-Control"]== "max-age=31536000"
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "unavailable-0704.0945v2", "paper-id-0704.0945", "not-public", "paper-id-0704.0945v2", "src"]
    assert all(" "+item+" " in keys for item in expected_keys)

    #eprint path also blocks
    resp = client_with_test_fs.get("/e-print/0704.0945v2")
    assert resp.status_code == 403
    assert 'Source Not Public' in resp.text
    assert headers["Surrogate-Control"]== 'max-age=31536000'
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "unavailable-0704.0945v2", "paper-id-0704.0945", "not-public", "paper-id-0704.0945v2", "src"]
    assert all(" "+item+" " in keys for item in expected_keys)

    #version that does not yet exist of encrypted papaer does not show as not public
    resp = client_with_test_fs.get("/src/0704.0945v3")
    assert resp.status_code == 404
    headers= resp.headers
    assert headers["Surrogate-Control"]== "max-age=604800"
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "unavailable-0704.0945v3", "paper-id-0704.0945", "paper-id-0704.0945v3", "src", "not-found"]
    assert all(" "+item+" " in keys for item in expected_keys)

def test_still_read_article(client_with_test_fs):
    #html blocked if source is encrypted/not public (but might not be converted)
    resp = client_with_test_fs.get("/html/0704.0380")
    assert resp.status_code != 403
    assert 'Source Not Public' not in resp.text
    headers= resp.headers
    assert headers["Surrogate-Control"]== "max-age=86400"
    keys= " "+headers["Surrogate-Key"]+" "
    assert " not_public " not in keys

    #pdf not blocked if source is encrypted/not public
    resp = client_with_test_fs.get("/pdf/0704.0380")
    assert resp.status_code != 403
    assert 'Source Not Public' not in resp.text
    headers= resp.headers
    assert headers["Surrogate-Control"]== "max-age=86400"
    keys= " "+headers["Surrogate-Key"]+" "
    assert " not_public " not in keys