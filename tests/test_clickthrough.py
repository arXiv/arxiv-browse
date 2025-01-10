import urllib.parse

from arxiv.base.urls.clickthrough import create_hash

def test_clickthrough(app_with_fake):
    client = app_with_fake.test_client()
    resp = client.get("/ct?url=http%3A%2F%2Fwww.example.com")
    assert resp.status_code == 404, "no v param"

    resp = client.get("/ct?v=bogus")
    assert resp.status_code == 404, "no URL param"

    resp = client.get("/ct")
    assert resp.status_code == 404

    resp = client.get("/ct?junk=totaljunk")
    assert resp.status_code == 404

    resp = client.get("/ct?url=http%3A%2F%2Fwww.example.com&v=bogus")
    assert resp.status_code == 404

    url = "https://example.com/something?whereis=thecheese"
    hash = create_hash(app_with_fake.config["CLICKTHROUGH_SECRET"], url)
    resp = client.get(f"/ct?v={hash}&url={urllib.parse.quote_plus(url)}")
