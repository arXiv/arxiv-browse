"""Integration tests

These do not run if not requested. Run with `pytest --runintegration`

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
