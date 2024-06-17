

def test_pdf_headers(client_with_test_fs):
    rv=client_with_test_fs.head("/pdf/cs/0011004")
    head=rv.headers["Surrogate-Key"]
    assert " pdf " in " "+head+" "
    assert "pdf-cs/0011004-current" in head
    assert "pdf-cs/0011004v" not in head
    assert "paper-id-cs/0011004" in head

    rv=client_with_test_fs.head("/pdf/cs/0011004v1")
    head=rv.headers["Surrogate-Key"]
    assert " pdf " in " "+head+" "
    assert "pdf-cs/0011004-current" not in head
    assert "pdf-cs/0011004v1" in head
    assert "paper-id-cs/0011004" in head