"""Integration tests

These do not run if not requested. Run with `pytest --runintegration`

These are run aginst localhost but that can be set by the env var HOST.

See the notes in tests/conftest.py
"""

import pytest
import requests
import os

@pytest.fixture
def host():
    return os.environ.get('HOST', 'http://localhost:8080')

@pytest.mark.integration
def test_new_pdf_only(host):
    resp = requests.head(f"{host}/pdf/1208.6335v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1208.6335v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/1208.6335v2")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1208.6335v2")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/1809.00949v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1809.00949v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

@pytest.mark.integration
def test_new_pdf_only_mutli_versions(host):
    resp = requests.head(f"{host}/pdf/2101.04792v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792v2")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v2")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792v3")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v3")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792v4")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v4")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_oldids_in_ps_cache(host):
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/acc-phys/9502001v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004v2")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004v2")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_oldids_pdf_only(host):
    resp = requests.head(f"{host}/pdf/cs/0212040v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0212040v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0212040")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0212040")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_pdf_only_v1_and_2_tex_v3(host):
    resp = requests.head(f"{host}/pdf/cs/0012007v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v1")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0012007v2")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v2")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0012007v3")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v3")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0012007")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_big_pdf(host):
    resp = requests.head(f"{host}/pdf/2209.08742v2")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2209.08742v2", stream=True)
    assert resp.status_code == 200

@pytest.mark.integration
def test_500(host):
    """These pdfs returned 500s during a test in 2022-12"""
    resp = requests.head(f"{host}/pdf/2104.02699v2")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2104.02699v2")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2104.13478v2")
    assert resp.status_code == 200
    resp = requests.get(f"{host}")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2108.11539v1")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2108.11539v1")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2112.10752v2")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2112.10752v2")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2209.08742v2")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2209.08742v2")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2210.03142v2")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2210.03142v2")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2212.07280v1")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2212.07280v1")
    assert resp.status_code == 200


@pytest.mark.integration
def test_timedout(host):
    """These pdfs returned timedout during a test in 2022-12"""
    resp = requests.head(f"{host}/pdf/2212.07879")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2212.07439")
    assert resp.status_code == 200


@pytest.mark.integration
def test_wdr(host):
    """These are some verisons that are withdrawls."""

    resp = requests.get(f"{host}/pdf/0911.3270v2")
    assert resp.status_code == 404 and b'withdrawn' in resp.content  # this version is wdr

    resp = requests.get(f"{host}/pdf/0911.3270v3")
    # paper exists but this version does not exist.
    # Does something similar to a withdrawn in that it returns a 404 and a message like
    # "source to generate pdf for this doesn't exist" but it should be a 404
    assert resp.status_code == 404 and b'unavailable' in resp.content

    resp = requests.get(f"{host}/pdf/2212.03351v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2212.03351v2")
    assert resp.status_code == 404 and b'unavailable' in resp.content


@pytest.mark.integration
def test_does_not_exist_without_version(host):
    """These are papers that don't exist. They were throwing `Max()
    arg is an empty sequence`"""
    resp = requests.get(f"{host}/pdf/0712.9999")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_with_version(host):
    """These are papers that don't exist."""
    resp = requests.get(f"{host}/pdf/0712.9999v1")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v23")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v1")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v23")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v1")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v3")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v1")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v3")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_pdf_only(host):
    """These are articles that exist but versions that don't exist for some pdf only submissions"""
    resp = requests.head(f"{host}/pdf/2101.04792v99")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0212040v99")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_ps_cache(host):
    """These are articles that exist but versions that don't exist for some tex submissions"""
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v9")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/acc-phys/9502001v99")
    assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.parametrize("arxiv_id",
[
        '1501.02398v2',
        '0910.1713v4', '1307.0741v2', '2008.09101v2',
        'cs/0606100v4', '2005.02207v2', '1901.07935v4', '1512.08657v3',
        'math/0010040v2', '1211.6961v4', '0709.3305v2', '2105.04405v2',
        '2110.12177v2', '1405.4051v2',
        '2009.11506v2', '2206.12790v2', '1710.04353v2',
        '2101.07819v3', '2106.13896v2', '2103.02343v2',
        '1606.05741v3', 'physics/0304034v2', '1608.00923v2',
        '2204.09099v2', '2212.08442v2', '1810.04862v2',
        '2009.11258v2', '2005.08944v3', '2001.04026v3', '1311.4906v2',
        '1011.6443v2', '0902.3052v2', 'gr-qc/9905068v4',
        '2103.15835v3', '1907.04856v2',
        '1407.4867v2', '1206.6183v2', '2106.00112v2', '2109.05182v2',
        '1610.01014v3', '1901.04988v2', '1306.4643v2', '1608.00134v2',
        '1803.07743v4', 'cs/0612028v2', '1401.1740v2', '1603.06209v2',
        '2112.02249v2', '2207.11705v3', '2208.13435v3',
        '2208.13514v2', '2106.03507v4', '1211.2296v4',
        'cond-mat/9810209v2', 'cond-mat/0212346v3', '1708.09372v2', ]
                         )
def test_withdrawn(host, arxiv_id):
    """Sample of withdrawn versions"""
    EXPECTED_WDR_STATUS = 404
    resp = requests.get(f"{host}/pdf/{arxiv_id}")
    assert resp.status_code == EXPECTED_WDR_STATUS and b"withdrawn" in resp.content
    resp = requests.get(f"{host}/src/{arxiv_id}")
    assert resp.status_code == EXPECTED_WDR_STATUS and b"withdrawn" in resp.content
    resp = requests.get(f"{host}/e-print/{arxiv_id}")
    assert resp.status_code == EXPECTED_WDR_STATUS and b"withdrawn" in resp.content


@pytest.mark.parametrize("arxiv_id", ['astro-ph/0306581v1', 'astro-ph/0306581'])
@pytest.mark.integration
def test_html_src(host, arxiv_id):
    resp = requests.get(f"{host}/html/{arxiv_id}")
    assert resp.status_code == 200 and b"The 2dF Galaxy Redshift Survey: Final Data Release" in resp.content
    resp = requests.get(f"{host}/html/{arxiv_id}/")
    assert resp.status_code == 200
    resp = requests.head(f"{host}/html/{arxiv_id}/survey_map_small.gif")
    assert resp.status_code == 200


@pytest.mark.integration
def test_html_src_withdrawn(host):
    """Submissions with HTML source"""
    # legacy returns 200 with msg: "Unavailable, The author has provided no source to generate PDF, and no PDF."
    # This is intentionally set to 500 in browse now to allow us to find
    # papers that might have this conditions but shouldn't
    # In the future this might get set to 404
    resp = requests.get(f"{host}/pdf/cond-mat/9906075v1")
    assert resp.status_code == 500 and b"file unavailable" in resp.content
    resp = requests.head(f"{host}/src/cond-mat/9906075v1")
    assert resp.status_code == 200

@pytest.mark.parametrize("arxiv_id, reason", [
    ("1808.02949v1",b"Authors provided incomplete file set"),
    ("1310.4962",b"font HeiseiKakuGo-W5-Bold is not embedded in several figures, causing permanent ps failure"),
    ("1310.4962v1",b"font HeiseiKakuGo-W5-Bold is not embedded in several figures, causing permanent ps failure"),
    ("1310.4962v2",b"font HeiseiKakuGo-W5-Bold is not embedded in several figures, causing permanent ps failure"),
    ("physics/0411006",b"pdftex submission + bundled ps and pdf files"),
    ("physics/0411006v1",b"pdftex submission + bundled ps and pdf files"),
    ("physics/0411006v2",b"pdftex submission + bundled ps and pdf files"),
    ("physics/0411006v3",b"pdftex submission + bundled ps and pdf files"),
])
@pytest.mark.integration
def test_reasons(host, arxiv_id, reason):
    """Paper in reasons"""
    msg = "Authors provided incomplete file set"
    resp = requests.get(f"{host}/pdf/{arxiv_id}")
    assert resp.status_code == 404
    assert reason in resp.content


@pytest.mark.integration
def test_404(host):
    """These returned 404s during a test in 2022-12"""
    resp = requests.get(f"{host}/pdf/1304.1682v1")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/1308.0729v1")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1302.1106v1")
    assert resp.status_code == 200


@pytest.mark.integration
def test_deleted(host):
    """Paper is deleted"""
    resp = requests.get(f"{host}/pdf/hep-ph/0509174")
    assert resp.status_code == 404
    assert "this identifier erroneously skipped during software upgrade" in resp.text

    resp = requests.get(f"{host}/pdf/hep-ph/0509174v1")
    assert resp.status_code == 404
    assert "this identifier erroneously skipped during software upgrade" in resp.text

    resp = requests.get(f"{host}/pdf/hep-ph/0509174v3")
    assert resp.status_code == 404
    assert "this identifier erroneously skipped during software upgrade" in resp.text

    # resp = requests.get(f"{host}/pdf/1310.4962")
    # assert resp.status_code == 404
    # assert msg in resp.text
    # resp = requests.get(f"{host}/pdf/1310.4962v1")
    # assert resp.status_code == 404
    # assert msg in resp.text
    # resp = requests.get(f"{host}/pdf/1310.4962v2")
    # assert resp.status_code == 404
    # assert msg in resp.text

    # resp = requests.get(f"{host}/pdf/physics/0411006")
    # assert resp.status_code == 404
    # assert msg in resp.text
    # resp = requests.get(f"{host}/pdf/physics/0411006")
    # assert resp.status_code == 404
    # assert msg in resp.text
    # resp = requests.get(f"{host}/pdf/physics/0411006")
    # assert resp.status_code == 404
    # assert msg in resp.text


@pytest.mark.integration
@pytest.mark.parametrize("etag, path",  [
    ("CO7+7eHNp/ICEAE=", "/src/2006.01705v1"),
    ("CLCsgOj30PUCEAE=", "/src/2006.01705v2"),
    ("CMm22Yi70vsCEAE=", "/src/2006.01705v3"),
    ("CPCD+Y3t8YEDEAI=", "/src/2006.01705v4"),
    ("CKjp75m5gYQDEAI=", "/src/2006.01705v5"),
    ("CPrJ5Jq5gYQDEAI=", "/src/2006.01705v6"),
    ])
def test_multi_version_src(host, etag, path):
    """Test for ARXIVCE-1455."""
    resp = requests.head(f"{host}{path}")
    assert resp and resp.status_code == 200 and etag in resp.headers["Etag"]
