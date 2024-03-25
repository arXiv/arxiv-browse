def test_html_paper(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/abs/2403.10561")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/2403.10561/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/2403.10561")
    assert resp.status_code == 200
    assert b"Human-Centric" in resp.data

    assert b"LIST:arXiv:2401.00907" in resp.data  # should have at least un-post-processed line

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


def test_html_paper_multi_html_files(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/abs/cs/9904010")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/cs/9904010/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/cs/9904010")
    assert resp.status_code == 200
    assert "html" in resp.headers["content-type"]
    txt = resp.data.decode()
    assert "The following files are available for cs/9904010" in txt
    assert "appendix.htm" in txt
    assert "report.htm" in txt
    assert "graph0.gif" not in txt
    assert "graph1.gif" not in txt
    assert "graph2.gif" not in txt
    assert "graph3.gif" not in txt
    assert "graph4.gif" not in txt
    assert "graph5.gif" not in txt

    resp = client_with_test_fs.get("/html/cs/9904010/report.htm")
    assert resp.status_code == 200
    assert b"Sample Characteristics and Response Rate" in resp.data
    assert "html" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9904010/appendix.htm")
    assert resp.status_code == 200
    assert b"Appendix: Survey Questions and Frequency of Responses" in resp.data
    assert "html" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9904010/graph1.gif")
    assert resp.status_code == 200
    assert "gif" in resp.headers["content-type"]
