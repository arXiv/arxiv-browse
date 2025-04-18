def test_html_paper(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/html/2403.10561")
    assert resp.status_code == 200
    headers= resp.headers
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")
    assert resp.headers.get('Link','') == "<https://arxiv.org/html/2403.10561>; rel='canonical'", "versionless canonical header"

    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["html", "paper-id-2403.10561", "paper-id-2403.10561-current", "html-native", "html-2403.10561-current"]
    assert all(" "+item+" " in keys for item in expected_keys)

    resp = client_with_test_fs.get("/html/2403.10561/shouldnotexist.html")
    assert resp.status_code == 404
    headers= resp.headers
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")
    keys= " "+headers["Surrogate-Key"]+" "
    expected_keys=["paper-unavailable", "unavailable-2403.10561-current", "paper-id-2403.10561", "paper-id-2403.10561-current", "not-found"]
    assert all(" "+item+" " in keys for item in expected_keys)

    resp = client_with_test_fs.get("/html/2403.10561")
    assert resp.status_code == 200 and b"Human-Centric" in resp.data

    assert b"LIST:arXiv:2401.00907" in resp.data  # should have at least un-post-processed line

    resp = client_with_test_fs.get("/html/2403.10561/")
    assert resp.status_code == 200 and b"Human-Centric" in resp.data
    assert resp.headers.get('Link','') == "<https://arxiv.org/html/2403.10561>; rel='canonical'", "versionless canonical header"

    resp = client_with_test_fs.get("/html/2403.10561v1")
    assert resp.status_code == 200 and b"Human-Centric" in resp.data
    assert resp.headers.get('Link','') == "<https://arxiv.org/html/2403.10561>; rel='canonical'", "versionless canonical header"

    resp = client_with_test_fs.get("/html/2403.10561v1/")
    assert resp.status_code == 200 and b"Human-Centric" in resp.data
    assert resp.headers.get('Link','') == "<https://arxiv.org/html/2403.10561>; rel='canonical'", "versionless canonical header"
    

def test_html_icon(client_with_test_fs):
    resp = client_with_test_fs.get("/html/2403.10561")
    assert resp.status_code == 200 and b"Human-Centric" in resp.data

    resp = client_with_test_fs.get("/html/2403.10561/icon.png")
    assert resp.status_code == 200 and resp.headers.get("Content-Type") == "image/png"
    assert not("Link" in resp.headers), "assets of html articles don't have a canonical header (yet?)"


def test_html_paper_multi_files(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/html/cs/9901011")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/cs/9901011/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/cs/9901011")
    assert resp.status_code == 200 and "A Brief History of the Internet" in resp.data.decode()
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011v1")
    assert resp.status_code == 200 and "A Brief History of the Internet" in resp.data.decode()
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011/")
    assert resp.status_code == 200 and "A Brief History of the Internet" in resp.data.decode()
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011v1/")
    assert resp.status_code == 200 and "A Brief History of the Internet" in resp.data.decode()
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011/ihist-isoc-v32.htm")
    assert resp.status_code == 200 and "A Brief History of the Internet" in resp.data.decode()
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9901011/timeline_v3.gif")
    assert resp.status_code == 200 and"gif" in resp.headers["content-type"]


def test_html_paper_multi_html_files(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/html/cs/9904010")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/cs/9904010/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/cs/9904010")
    assert resp.status_code == 200
    assert "text/html; charset=utf-8" in resp.headers["content-type"]
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
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9904010/appendix.htm")
    assert resp.status_code == 200
    assert b"Appendix: Survey Questions and Frequency of Responses" in resp.data
    assert "text/html; charset=utf-8" in resp.headers["content-type"]

    resp = client_with_test_fs.get("/html/cs/9904010/graph1.gif")
    assert resp.status_code == 200
    assert "gif" in resp.headers["content-type"]

def test_html_headers(client_with_test_fs):
    """Test html content type also declares encoding."""
    resp = client_with_test_fs.head("/html/2403.10561")
    assert resp.status_code == 200
    assert 'Content-Type' in resp.headers
    content_type = resp.headers.get('Content-Type', '')
    assert content_type== "text/html; charset=utf-8"
    assert resp.headers.get('Link', '') == "<https://arxiv.org/html/2403.10561>; rel='canonical'", "versionless canonical header"

    #Surrogate Keys
    rv=client_with_test_fs.head("/html/2403.10561")
    head=rv.headers["Surrogate-Key"]
    assert " html " in " "+head+" "
    assert "html-2403.10561-current" in head
    assert "html-2403.10561v" not in head
    assert "paper-id-2403.10561" in head
    assert "html-native" in head
    assert "html-latexml" not in head

    rv=client_with_test_fs.head("/html/cs/9904010v1/graph1.gif")
    assert not('Link' in rv.headers), "HTML assets do not have a canonical header (yet?)"
    head=rv.headers["Surrogate-Key"]
    assert " html " in " "+head+" "
    assert "html-cs/9904010-current" not in head
    assert "html-cs/9904010v1" in head
    assert "paper-id-cs/9904010" in head
    assert "html-native" in head
    assert "html-latexml" not in head
