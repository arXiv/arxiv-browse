def test_html_paper(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/abs/2403.10561")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/2403.10561/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/2403.10561")
    assert resp.status_code == 200
    assert "Human-Centric" in resp.data.decode()

def test_html_paper_multi_files(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/abs/cs/9901011")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/cs/9901011/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/cs/9901011")
    assert resp.status_code == 200
    assert "A Brief History of the Internet" in resp.data.decode()
    assert "html" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011/ihist-isoc-v32.htm")
    assert resp.status_code == 200
    assert "A Brief History of the Internet" in resp.data.decode()
    assert "html" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011/timeline_v3.gif")
    assert resp.status_code == 200
    assert "gif" in resp.headers["content-type"]
