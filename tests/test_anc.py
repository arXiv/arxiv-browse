"""Tests related to ancillary files"""
import pytest
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime


# TODO
# test 404, withdrawn, nonexistant version
# paper without anc

def test_anc_on_abs_page(client_with_test_fs):
    client = client_with_test_fs
    rv = client.get('/abs/physics/9707012')
    assert rv.status_code == 200
    assert 'ancillary' not in rv.data.decode('utf-8')

    rv = client.get('/abs/1601.04345')
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
    ancdiv = html.find('div', {'class': 'ancillary'})
    assert ancdiv

    rawhtml = str(ancdiv)
    for link in ["CDA_Derivative.m",
                 "Integration_Example_System.m",
                 "Kepler_E_of_f_e.m",
                 "Quadrupole_Pout_Oscillation.m",
                 "Quadrupole_Pout_Oscillation_jz.m",
                 "Quadrupole_Pout_Oscillation_jz_maxmin.m"]:
        assert link in rawhtml


def test_anc_listing(client_with_test_fs):
    client = client_with_test_fs
    rv = client.get('/src/1601.04345/anc')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    for link in ["CDA_Derivative.m",
                 "Integration_Example_System.m",
                 "Kepler_E_of_f_e.m",
                 "Quadrupole_Pout_Oscillation.m",
                 "Quadrupole_Pout_Oscillation_jz.m",
                 "Quadrupole_Pout_Oscillation_jz_maxmin.m"]:
        assert link in data


def test_anc_listing_no_anc_files(client_with_test_fs):
    client = client_with_test_fs
    for link in ["/src/physics/9707012/anc",
                 "/src/physics/9707012/anc/Integration_Example_System.m",
                 "/src/physics/9707012/anc/",
                 ]:
        rv = client.get(link)
        assert link and rv.status_code == 404


paths_1601 = [
    ("/src/1601.04345v2/anc/CDA_Derivative.m", 200, 2035),
    ("/src/1601.04345v2/anc/Integration_Example_System.m", 200,3747),
    ("/src/1601.04345v2/anc/Kepler_E_of_f_e.m", 200, 178),
    ("/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation.m", 200, 1291),
    ("/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation_jz.m", 200, 772),
    ("/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation_jz_maxmin.m", 200, 985),
    ("/src/1601.04345v2/anc/bogus-should-not-exist", 404, False),
]

@pytest.mark.parametrize("path,status,bytes", paths_1601)
def test_1601_04345_anc_files(client_with_test_fs, path, status, bytes):
    rv = client_with_test_fs.get(path)
    assert rv.status_code == status
    if status == 200:
        assert rv.headers["Accept-Ranges"] == "bytes"  # Must do Accept-Ranges for CDNs
        assert int(rv.headers["Content-Length"]) == bytes  # CDNs need length
        assert parsedate_to_datetime(rv.headers["Last-Modified"])  # just check that it parses

ranges = [
    ("00", "00", b"f"),
    ("00", "07", b"function"),
    ("00", "af",
     b"function [jz_oscmax,jz_oscmin] = Quadrupole_Pout_Oscillation_jz_maxmin(ep_SA,eper,jt,et)\r\n"
     b"%calculate the fast oscillating component from slowly evolving component bar_j_e_vec\r\n"
     ),
    ("349", "3d8",
     b"om_osc=atan2(S,-C);\r\n"
     b"%jz_osc = sin1.*sin(ft)+cos1.*cos(ft)+sin2.*sin(2*ft)+...\r\n"
     b"%    cos2.*cos(2*ft)+sin3.*sin(3*ft)+cos3.*cos(3*ft);\r\n"
     b"\r\n"
     b"end\r\n\r\n"
     ),
]
@pytest.mark.parametrize("start,end,bytes", ranges)
def test_1601_04345_anc_range_request_bytes(client_with_test_fs, start, end, bytes):
    resp = client_with_test_fs.get("/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation_jz_maxmin.m",
                                   headers={"Range": f"bytes={int(start,16)}-{int(end,16)}"})
    assert resp.status_code == 206
    assert resp.data == bytes


def test_anc_headers(client_with_test_fs):
    client = client_with_test_fs

    rv = client.get('/src/1601.04345/anc')
    head=rv.headers["Surrogate-Key"]
    assert "anc" in head
    assert "paper-id-1601.04345-current" in head
    assert "src-1601.04345-current" in head
    assert "anc-1601.04345-current" in head
    assert "paper-id-1601.04345v" not in head
    assert "paper-id-1601.04345" in head

    rv = client.get('/src/1601.04345v2/anc')
    head=rv.headers["Surrogate-Key"]
    assert "anc" in head
    assert "paper-id-1601.04345-current" not in head
    assert "paper-id-1601.04345v2" in head
    assert "src-1601.04345v2" in head
    assert "anc-1601.04345v2" in head
    assert "paper-id-1601.04345" in head

    rv = client.get('/src/1601.04345/anc/Integration_Example_System.m')
    head=rv.headers["Surrogate-Key"]
    assert "anc" in head
    assert "paper-id-1601.04345-current" in head
    assert "src-1601.04345-current" in head
    assert "anc-1601.04345-current" in head
    assert "paper-id-1601.04345v" not in head
    assert "paper-id-1601.04345" in head

    rv = client.get('/src/1601.04345v2/anc/Integration_Example_System.m')
    head=rv.headers["Surrogate-Key"]
    assert "anc" in head
    assert "paper-id-1601.04345-current" not in head
    assert "paper-id-1601.04345v2" in head
    assert "paper-id-1601.04345" in head
    assert "src-1601.04345v2" in head
    assert "anc-1601.04345v2" in head
