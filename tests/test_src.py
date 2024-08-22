"""Test of the /src path."""
from email.utils import parsedate_to_datetime

import pytest

files="""ftp/cond-mat/papers/9805/9805021.gz
ftp/arxiv/papers/1601/1601.04345.tar.gz
ftp/arxiv/papers/2101/2101.10016.gz
ftp/arxiv/papers/2310/2310.08262.html.gz
ftp/arxiv/papers/1208/1208.9999.gz
ftp/cs/papers/0012/0012007.tar.gz
ftp/cs/papers/0011/0011004.gz
orig/cond-mat/papers/9805/9805021v1.ps.gz
orig/arxiv/papers/1601/1601.04345v1.tar.gz
orig/cs/papers/0011/0011004v1.gz"""

"""
ftp/cond-mat/papers/9805/9805021.gz

ftp/arxiv/papers/1809/1809.00949.pdf
ftp/arxiv/papers/1601/1601.04345.tar.gz
ftp/arxiv/papers/2101/2101.10016.gz
ftp/arxiv/papers/2101/2101.04792.pdf
ftp/arxiv/papers/2310/2310.08262.html.gz
ftp/arxiv/papers/1208/1208.6335.pdf
ftp/arxiv/papers/1208/1208.9999.gz

ftp/cs/papers/0012/0012007.tar.gz
ftp/cs/papers/0212/0212040.pdf
ftp/cs/papers/0011/0011004.gz
"""

cases = [
    ["cond-mat/9805021", "arXiv-cond-mat9805021v2.gz", "single file .gz"],
    ["1809.00949", "arXiv-1809.00949v1.pdf", ".pdf only"],
    ["1601.04345", "arXiv-1601.04345v2.tar.gz", ".tar.gz with anc files, 2 versions"],
    ["2101.04792", "arXiv-2101.04792v4.pdf", ".pdf only"],
    ["2101.10016v1", "2101.10016v1.tar.gz", "current version wdr, ver 8 wdr"],
    ["2101.10016v2", "2101.10016v2.tar.gz", "current version wdr"],
    ["2101.10016v3", "2101.10016v3.tar.gz", "current version wdr"],
    ["2101.10016v4", "2101.10016v4.tar.gz", "current version wdr"],
    ["2101.10016v5", "2101.10016v5.tar.gz", "current version wdr"],
    ["2101.10016v6", "2101.10016v6.tar.gz", "current version wdr"],
    ["2101.10016v7", "2101.10016v7.tar.gz", "current version wdr"],
    #["1208.9999", "1208.9999"],
    ["cs/0012007", "cs0012007", ""],

    ["cond-mat/9805021v1", "cond-mat9805021v1.ps.gz", "gzipped ps"],
    ["cond-mat/9805021", "cond-mat9805021v2.gz", "gzipped ps"],
    ["cond-mat/9805021v2", "cond-mat9805021v2.gz", "gzipped ps"],

    ["cs/0012007", "cs0012007v3.tar.gz", "leading zero"],
    ["cs/0012007v3", "cs0012007v3.tar.gz", "leading zero"],
    ["cs/0012007v2", "cs0012007v2.pdf", "leading zero"],
    ["cs/0012007v1", "cs0012007v1.pdf", "leading zero"],

    ["1601.04345v1", "1601.04345v1.tar.gz", ""],
    ["cs/0012007", "cs0012007v3.tar.gz", ""],
    # ["cs/0011004", "cs-0011004"], # single file gz paper but bad gzip file
    # ["cs/0011004v1", "cs-0011004v1"],  # single file gz paper but bad gzip file
]

@pytest.mark.parametrize("path,paperid,expected_file,desc", [ ["/src/"]+c for c in cases] )
def test_src(client_with_test_fs, path, paperid, expected_file, desc ):
    client = client_with_test_fs
    resp = client.get(path + paperid)
    assert resp
    assert resp.status_code == 200
    assert resp.headers["Accept-Ranges"] == "bytes"  # Must do Accept-Ranges for Fastly CDN large objs
    assert resp.headers["Transfer-Encoding"] == "chunked" # Must do chunked on a raw get for Cloud run large obj
    assert expected_file in resp.headers["Content-Disposition"]
    assert "v" in resp.headers["Content-Disposition"]  # want the v in both current and v requests
    assert "/" not in resp.headers["Content-Disposition"]  # nobody wants a slash in their file name
    assert parsedate_to_datetime(resp.headers["Last-Modified"])  # just check that it parses

    resp = client.head(path + paperid)
    assert resp
    assert resp.status_code == 200
    assert resp.headers["Accept-Ranges"] == "bytes"  # Must do Accept-Ranges for Fastly CDN large objs
    assert expected_file in resp.headers["Content-Disposition"]
    assert "v" in resp.headers["Content-Disposition"]  # want the v in both current and v requests
    assert "/" not in resp.headers["Content-Disposition"]  # nobody wants a slash in their file name
    assert parsedate_to_datetime(resp.headers["Last-Modified"])  # just check that it parses
    #different than get:
    assert "Content-Length" in resp.headers

    resp = client.get(path + paperid, headers={"Range": "0-1"})
    assert resp
    assert resp.status_code == 206 or resp.status_code == 416


def test_src_version_not_found(client_with_test_fs):
    resp = client_with_test_fs.get("/src/cond-mat/9805021v9")
    assert resp.status_code == 404
    resp = client_with_test_fs.get("/src/2101.10016v9")
    assert resp.status_code == 404
    resp = client_with_test_fs.get("/src/2101.10016v10")
    assert resp.status_code == 404

def test_wdr_current_src(client_with_test_fs):
    """Current source of a wdr paper should be 404.

    The 2101.10016 papers in test_src represent reqeusts get earlier version src
    for a wdr paper.
    """
    resp = client_with_test_fs.get("/src/2101.10016")
    assert resp.status_code == 404

    # .html.gz only one version and it is wdr
    resp = client_with_test_fs.get("/src/2310.08262")
    assert resp.status_code == 404

    resp = client_with_test_fs.get("/html/2310.08262")
    assert resp.status_code == 404


def test_src_headers(client_with_test_fs):
    client=client_with_test_fs

    rv=client.head("/src/1601.04345")
    head=rv.headers["Surrogate-Key"]
    assert "src" in head
    assert "paper-id-1601.04345-current" in head
    assert "paper-id-1601.04345v" not in head
    assert "paper-id-1601.04345 " in head+" "

    rv=client.head("/src/1601.04345v2")
    head=rv.headers["Surrogate-Key"]
    assert "src" in head
    assert "paper-id-1601.04345-current" not in head
    assert "paper-id-1601.04345v2" in head
    assert "paper-id-1601.04345 " in head+" "
   
