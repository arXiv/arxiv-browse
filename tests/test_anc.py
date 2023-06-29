"""Tests related to ancillary files"""
from bs4 import BeautifulSoup


def test_anc_on_abs_page(client_with_test_fs):
    client = client_with_test_fs
    rv = client.get('/abs/1601.04345')
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
    ancdiv = html.find('div', {'class': 'ancillary'})
    assert ancdiv

    rawhtml = str(ancdiv)
    for link in ["/anc/1601.04345v2/CDA_Derivative.m",
                 "/anc/1601.04345v2/Integration_Example_System.m",
                 "/anc/1601.04345v2/Kepler_E_of_f_e.m",
                 "/anc/1601.04345v2/Quadrupole_Pout_Oscillation.m",
                 "/anc/1601.04345v2/Quadrupole_Pout_Oscillation_jz.m",
                 "/anc/1601.04345v2/Quadrupole_Pout_Oscillation_jz_maxmin.m"]:
        assert link in rawhtml


def test_1601_04345_anc_files(client_with_test_fs):
    client = client_with_test_fs
    for link in ["/anc/1601.04345v2/CDA_Derivative.m",
                 "/anc/1601.04345v2/Integration_Example_System.m",
                 "/anc/1601.04345v2/Kepler_E_of_f_e.m",
                 "/anc/1601.04345v2/Quadrupole_Pout_Oscillation.m",
                 "/anc/1601.04345v2/Quadrupole_Pout_Oscillation_jz.m",
                 "/anc/1601.04345v2/Quadrupole_Pout_Oscillation_jz_maxmin.m"]:
        rv = client.get(link)
        assert rv.status_code == 200
