

def test_pdf_reasons(client_with_test_fs):
    resp=client_with_test_fs.get("/pdf/0704.0001v1")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704126")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704126v1")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704126v2")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704126v23")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704998")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704998v1")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704998v10")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704998v100")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704999v1")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/cond-mat/9704999v2")
    assert  "reason" not in resp.text and "unit test" not in resp.text

    resp=client_with_test_fs.get("/pdf/0804.9999v99")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/0804.9999")
    assert  "reason" not in resp.text and "unit test" not in resp.text

    resp=client_with_test_fs.get("/pdf/1506.99999v1")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/1506.99998")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/1506.99998v1")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/1506.99998v10")
    assert  "reason" in resp.text and "unit test" in resp.text

    resp=client_with_test_fs.get("/pdf/1506.99998v100")
    assert  "reason" in resp.text and "unit test" in resp.text

