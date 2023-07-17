"""Tests related to ancillary files"""
from bs4 import BeautifulSoup


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


def test_1601_04345_anc_files(client_with_test_fs):
    client = client_with_test_fs
    for link in ["/src/1601.04345v2/anc/CDA_Derivative.m",
                 "/src/1601.04345v2/anc/Integration_Example_System.m",
                 "/src/1601.04345v2/anc/Kepler_E_of_f_e.m",
                 "/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation.m",
                 "/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation_jz.m",
                 "/src/1601.04345v2/anc/Quadrupole_Pout_Oscillation_jz_maxmin.m"]:
        rv = client.get(link)
        assert link and rv.status_code == 200

        rsp = client.get("/src/1601.04345v2/anc/bogus-should-not-exist")
        assert rsp.status_code == 404
