

def test_pdf_headers(client_with_test_fs):
    rv=client_with_test_fs.head("/pdf/cs/0011004")
    head=rv.headers["Surrogate-Key"]
    assert " pdf " in " "+head+" "
    assert "pdf-cs/0011004-current" in head
    assert "pdf-cs/0011004v" not in head
    assert "paper-id-cs/0011004" in head

    assert rv.headers["Link"] == "<https://arxiv.org/pdf/cs/0011004>; rel='canonical'"

    rv=client_with_test_fs.head("/pdf/cs/0011004v1")
    head=rv.headers["Surrogate-Key"]
    assert " pdf " in " "+head+" "
    assert "pdf-cs/0011004-current" not in head
    assert "pdf-cs/0011004v1" in head
    assert "paper-id-cs/0011004" in head

    assert rv.headers["Link"] == "<https://arxiv.org/pdf/cs/0011004v1>; rel='canonical'", "should not have version"


def test_pdf_redirect(client_with_test_fs):
    rv=client_with_test_fs.head("/pdf/cs/0011004v1?crazy_query_string=notgood")
    assert rv.status_code == 301
    assert rv.headers["Location"] == "http://localhost/pdf/cs/0011004v1"

    rv = client_with_test_fs.head("/pdf/2201.0001?crazy_query_string=notgood")
    assert rv.status_code == 301
    assert rv.headers["Location"] == "http://localhost/pdf/2201.0001"