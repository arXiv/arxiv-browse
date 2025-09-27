from email.utils import parsedate_to_datetime
import pytest

cases = [

]


def test_ps(dbclient):

    path = "/ps/"
    client = dbclient
    paperid, expectedfile = "cond-mat/9805021v1", "cond-mat9805021v1.ps"
    resp = client.get("/abs/" + paperid)
    assert resp.status_code == 200 and "PS Source" in resp.text

    resp = client.get(path + paperid)
    assert resp
    assert resp.status_code == 200
    assert resp.headers["Accept-Ranges"] == "bytes"  # Must do Accept-Ranges for Fastly CDN large objs
    assert resp.headers["Transfer-Encoding"] == "chunked" # Must do chunked on a raw get for Cloud run large ob
    assert expectedfile in resp.headers["Content-Disposition"]
    assert "v" in resp.headers["Content-Disposition"]  # want the v in both current and v requests
    assert  "max-age=31536000" in resp.headers.get("Surrogate-Control")

    resp = client.head(path + paperid)
    assert resp
    assert resp.status_code == 200
    assert resp.headers["Accept-Ranges"] == "bytes"  # Must do Accept-Ranges for Fastly CDN large objs
    assert expectedfile in resp.headers["Content-Disposition"]
    assert "v" in resp.headers["Content-Disposition"]  # want the v in both current and v requests
    assert "/" not in resp.headers["Content-Disposition"]  # nobody wants a slash in their file name
    assert parsedate_to_datetime(resp.headers["Last-Modified"])  # just check that it parses
    #different than get:
    assert "Content-Length" in resp.headers
    assert "max-age=31536000" in resp.headers.get("Surrogate-Control")

    resp = client.get(path + paperid, headers={"Range": "0-1"})
    assert resp
    assert resp.status_code == 206 or resp.status_code == 416

def test_non_ps(dbclient):
    path = "/ps/cond-mat/9805021v2"
    client = dbclient
    resp = client.get(path)
    assert resp and resp.status_code == 404
    resp = client.head(path)
    assert resp and resp.status_code == 404
    resp = client.get(path, headers={"Range": "0-1"})
    assert resp and resp.status_code == 404
