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
    resp = requests.get(f"{host}/pdf/2104.13478v2")
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


@pytest.mark.xfail(reason="not yet fixed, But these URLs should never be shown to users by the arxiv system")
@pytest.mark.integration
def test_wdr(host):
    """These are some verisons that are withdrawls."""

    resp = requests.get(f"{host}/pdf/0911.3270v2.pdf")
    assert resp.status_code == 200 # this version is wdr and in the legacy sytem does a 200 with a message like "paper not available"

    resp = requests.get(f"{host}/pdf/0911.3270v3.pdf")
    assert resp.status_code == 404 # this version does not exist. The legacy system does something similar to v2

    resp = requests.get(f"{host}/pdf/2212.03351v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2212.03351v2.pdf")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_without_version(host):
    """These are papers that don't exist. They were throwing `Max()
    arg is an empty sequence`"""
    resp = requests.get(f"{host}/pdf/0712.9999")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999.pdf")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_with_version(host):
    """These are papers that don't exist."""
    resp = requests.get(f"{host}/pdf/0712.9999v1")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v23")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v1.pdf")
    assert resp.status_code == 404

    resp = requests.get(f"{host}/pdf/0712.9999v23.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v1")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v3")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v1.pdf")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0011999v3.pdf")
    assert resp.status_code == 404


@pytest.mark.xfail(reason="not yet fixed, see TODO in arxiv_dissemination.path_for_id.current_pdf_path()")
@pytest.mark.integration
def test_does_not_exist_pdf_only(host):
    """These are articles that exist but versions that don't exist for some pdf only submissions"""
    resp = requests.head(f"{host}/pdf/2101.04792v99.pdf")
    assert resp.status_code == 404
    resp = requests.head(f"{host}/pdf/2101.04792v99")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/cs/0212040v99.pdf")
    assert resp.status_code == 404
    resp = requests.head(f"{host}/pdf/cs/0212040v99")
    assert resp.status_code == 404


@pytest.mark.integration
def test_does_not_exist_ps_cache(host):
    """These are articles that exist but versions that don't exist for some tex submissions"""
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v9.pdf")
    assert resp.status_code == 404
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v9")
    assert resp.status_code == 404

    resp = requests.head(f"{host}/pdf/acc-phys/9502001v99.pdf")
    assert resp.status_code == 404
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v99")
    assert resp.status_code == 404
