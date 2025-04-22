
def test_nonsense_identifier(dbclient):
    resp = dbclient.get("/abs/abcde")
    assert resp.status_code == 404
    assert "Invalid article identifier" in resp.text

def test_encrypted_source_fs(client_with_test_fs):
    """Tests that there is no link for source files on the abs page if the file is encrypted"""
    resp = client_with_test_fs.get("/abs/0704.0380")
    assert resp.status_code == 200
    assert 'TeX Source' not in resp.text
    assert 'https://arxiv.org/src/2405.19135' not in resp.text

    resp = client_with_test_fs.get("/abs/0704.0945v2")
    assert resp.status_code == 200
    assert 'TeX Source' not in resp.text
    assert 'https://arxiv.org/src/0704.0945v2' not in resp.text

def test_encrypted_source_db(dbclient):
    """Tests that there is no link for source files on the abs page if the file is encrypted"""
    resp = dbclient.get("/abs/1101.5805v2")
    assert resp.status_code == 200
    assert 'TeX Source' not in resp.text
    assert 'https://arxiv.org/src/1101.5805' not in resp.text 

    resp = dbclient.get("/abs/1102.0333")
    assert resp.status_code == 200
    assert 'TeX Source' not in resp.text
    assert 'https://arxiv.org/src/1102.0333' not in resp.text

