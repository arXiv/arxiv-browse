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
    resp = requests.head(f"{host}/pdf/1208.6335v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1208.6335v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/1208.6335v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1208.6335v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/1809.00949v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1809.00949v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

@pytest.mark.integration
def test_new_pdf_only_mutli_versions(host):
    resp = requests.head(f"{host}/pdf/2101.04792v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792v3.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v3.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792v4.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v4.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/2101.04792.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_oldids_in_ps_cache(host):
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/acc-phys/9502001v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_oldids_pdf_only(host):
    resp = requests.head(f"{host}/pdf/cs/0212040v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0212040v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0212040.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0212040.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_pdf_only_v1_and_2_tex_v3(host):
    resp = requests.head(f"{host}/pdf/cs/0012007v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0012007v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0012007v3.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v3.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']

    resp = requests.head(f"{host}/pdf/cs/0012007.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']


@pytest.mark.integration
def test_big_pdf(host):
    resp = requests.head(f"{host}/pdf/2209.08742v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2209.08742v2.pdf", stream=True)
    assert resp.status_code == 200

@pytest.mark.integration
def test_500(host):
    """These pdfs returned 500s during a test in 2022-12"""
    resp = requests.head(f"{host}/pdf/2104.02699v2.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2104.02699v2.pdf")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2104.13478v2.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2104.13478v2.pdf")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2108.11539v1.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2108.11539v1.pdf")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2112.10752v2.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2112.10752v2.pdf")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2209.08742v2.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2209.08742v2.pdf")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2210.03142v2.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2210.03142v2.pdf")
    assert resp.status_code == 200

    resp = requests.head(f"{host}/pdf/2212.07280v1.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2212.07280v1.pdf")
    assert resp.status_code == 200


@pytest.mark.integration
def test_timedout(host):
    """These pdfs returned timedout during a test in 2022-12"""
    resp = requests.head(f"{host}/pdf/2212.07879.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/2212.07439.pdf")
    assert resp.status_code == 200


@pytest.mark.integration
def test_wdr(host):
    """These are some verisons that are withdrawls."""

    resp = requests.get(f"{host}/pdf/0911.3270v2.pdf")
    assert resp.status_code == 200 # this version is wdr and in the legacy sytem does a 200 with a message like "paper not available"

    resp = requests.get(f"{host}/pdf/0911.3270v3.pdf")
    # paper exists but this version does not exist. The legacy system
    # does something similar to a withdrawn in that it retunrs a 200 and a message like
    # "source to generate pdf for this doesn't exist" but it should be a 404
    assert resp.status_code == 200
    assert 'unavailable' in resp.text

    resp = requests.get(f"{host}/pdf/2212.03351v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2212.03351v2.pdf")
    assert resp.status_code == 200
    assert 'unavailable' in resp.text


@pytest.mark.integration
def test_does_not_exist_without_version(host):
    """These are papers that don't exist. They were throwing `Max()
    arg is an empty sequence`"""
    resp = requests.get(f"{host}/pdf/0712.9999.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999.pdf")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_with_version(host):
    """These are papers that don't exist."""
    resp = requests.get(f"{host}/pdf/0712.9999v1.pdf")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v23.pdf")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v1.pdf")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v23.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v1.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v3.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v1.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v3.pdf")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_pdf_only(host):
    """These are articles that exist but versions that don't exist for some pdf only submissions"""
    resp = requests.head(f"{host}/pdf/2101.04792v99.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0212040v99.pdf")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_ps_cache(host):
    """These are articles that exist but versions that don't exist for some tex submissions"""
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v9.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/acc-phys/9502001v99.pdf")
    assert resp.status_code == 404


@pytest.mark.integration
def test_withdrawn(host):
    """Sample of withdrawn versions"""
    EXPECTED_WDR_STATUS = 200
    def integration_test_of_withdrawn(arxiv_id):
        resp = requests.get(f"{host}/pdf/{arxiv_id}.pdf")
        assert resp.status_code == EXPECTED_WDR_STATUS, f"For withdrawn paper {arxiv_id} HTTP status code should have been {EXPECTED_WDR_STATUS} but was {resp.status_code}"
        assert "The author has provided no source" in resp.text, f"For withdrawn paper {arxiv_id} the expected message was not found in the response"

    wdr_ids =[
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

    for arxiv_id in wdr_ids:
        integration_test_of_withdrawn(arxiv_id)


@pytest.mark.xfail(reason="not yet implemented")
@pytest.mark.integration
def test_html_src(host):
    """Submissions with HTML source"""
    # legacy returns 200 with msg: "Unavailable, The author has provided no source to generate PDF, and no PDF."
    resp = requests.get(f"{host}/pdf/cond-mat/9906075v1.pdf")
    assert resp.status_code == 404

    html_src = 'astro-ph/0306581v1.pdf'


@pytest.mark.xfail(reason="sync problem, does not exist on bucket yet")
@pytest.mark.integration
def test_404(host):
    """These returned 404s during a test in 2022-12"""
    resp = requests.get(f"{host}/pdf/1304.1682v1.pdf")
    assert resp.status_code == 200
    resp = requests.get(f"{host}/pdf/1308.0729v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1302.1106v1.pdf")
    assert resp.status_code == 200
