def test_new_pdf_only(client_with_test_fs):
    resp = client_with_test_fs.get("/pdf/1208.6335v1.pdf")
    assert "1208.6335v1" in resp.text

    resp = client_with_test_fs.get("/pdf/1208.6335v2.pdf")
    assert "1208.6335v2" in resp.text

    resp = client_with_test_fs.get("/pdf/1809.00949v1.pdf")
    assert "1809.00949v1" in resp.text


def test_new_pdf_only_mutli_versions(client_with_test_fs):
    resp = client_with_test_fs.get("/pdf/2101.04792v1.pdf")
    assert "2101.04792v1" in resp.text

    resp = client_with_test_fs.get("/pdf/2101.04792v2.pdf")
    assert "2101.04792v2" in resp.text

    resp = client_with_test_fs.get("/pdf/2101.04792v3.pdf")
    assert "2101.04792v3" in resp.text

    resp = client_with_test_fs.get("/pdf/2101.04792v4.pdf")
    assert "2101.04792v4" in resp.text

    resp = client_with_test_fs.get("/pdf/2101.04792.pdf")
    assert "2101.04792v4" in resp.text
