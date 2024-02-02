
def test_oldids_in_ps_cache(client_with_test_fs):
    resp = client_with_test_fs.get("/pdf/acc-phys/9502001v1")
    assert "9502001v1" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0011004v1")
    assert "0011004v1" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0011004v2")
    assert "0011004v2" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0011004")
    assert "0011004v2" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0011004")
    assert "0011004v2" in resp.text


def test_oldids_pdf_only(client_with_test_fs):
    resp = client_with_test_fs.get("/pdf/cs/0212040v1")
    assert resp.status_code == 200
    assert "0212040v1" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0212040")
    assert resp.status_code == 200
    assert "0212040v1" in resp.text


def test_pdf_only_v1_and_2_tex_v3(client_with_test_fs):
    resp = client_with_test_fs.get("/pdf/cs/0012007v1")
    assert "0012007v1" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0012007v2")
    assert "0012007v2" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0012007v3")
    assert "0012007v3" in resp.text

    resp = client_with_test_fs.get("/pdf/cs/0012007")
    assert "0012007v3" in resp.text
