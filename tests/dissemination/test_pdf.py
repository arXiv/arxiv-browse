

def test_pdf_headers(client_with_test_fs):
    #client=client_with_test_fs

    rv=client_with_test_fs.head("/pdf/cs/0011004")
    head=rv.headers["Surrogate-Key"]
    assert " pdf " in " "+head+" "
    assert "pdf-unversioned" in head
    assert "pdf-versioned" not in head
    assert "paper-id-cs/0011004" in head

    rv=client_with_test_fs.head("/pdf/cs/0011004v1")
    head=rv.headers["Surrogate-Key"]
    assert " pdf " in " "+head+" "
    assert "pdf-unversioned" not in head
    assert "pdf-versioned" in head
    assert "paper-id-cs/0011004" in head