def test_html_paper(client_with_test_fs):
    """Test a paper with html source."""
    resp = client_with_test_fs.head("/abs/2403.10561")
    assert resp.status_code == 200

    resp = client_with_test_fs.get("/html/2403.10561/shouldnotexist.html")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/2403.10561")
    assert resp.status_code == 200
    assert "Human-Centric" in resp.data.decode()
