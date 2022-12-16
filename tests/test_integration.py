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
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/1208.6335v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1208.6335v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/1809.00949v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/1809.00949v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

@pytest.mark.integration
def test_new_pdf_only_mutli_versions(host):
    resp = requests.head(f"{host}/pdf/2101.04792v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/2101.04792v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/2101.04792v3.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v3.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/2101.04792v4.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792v4.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/2101.04792.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/2101.04792.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024


@pytest.mark.integration
def test_oldids_in_ps_cache(host):
    resp = requests.head(f"{host}/pdf/acc-phys/9502001v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/acc-phys/9502001v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0011004v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0011004v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0011004.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024


@pytest.mark.integration
def test_oldids_pdf_only(host):
    resp = requests.head(f"{host}/pdf/cs/0212040v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0212040v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0212040.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0212040.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024


@pytest.mark.integration
def test_pdf_only_v1_and_2_tex_v3(host):
    resp = requests.head(f"{host}/pdf/cs/0012007v1.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v1.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0012007v2.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v2.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0012007v3.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007v3.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024

    resp = requests.head(f"{host}/pdf/cs/0012007.pdf")
    assert resp.status_code == 200

    resp = requests.get(f"{host}/pdf/cs/0012007.pdf")
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers['content-type']
    assert int(resp.headers['content-length']) > 1024


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
