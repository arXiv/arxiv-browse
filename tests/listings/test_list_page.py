import pytest
import re
from datetime import date
from unittest.mock import MagicMock
from unittest import mock

from browse.controllers import list_page

from browse.services.listing import NotModifiedResponse, get_listing_service
from bs4 import BeautifulSoup


def test_basic_lists(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/hep-ph/2009")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/hep-ph/new")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/hep-ph/current")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/hep-ph/pastweek")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/hep-ph/recent")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/hep-ph/2009-01?skip=925&show=25")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/astro-ph/2004")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/math/1992")
    assert rv.status_code == 200
    assert rv.headers.get("Surrogate-Control", None) != None

    rv = client.get("/list/math/1992-01")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-01")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-02")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-03")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-04")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-05")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-06")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-07")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-08")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-09")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-10")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-11")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-12")
    assert rv.status_code == 200

    rv = client.get("/list/math/2001")
    assert rv.status_code == 200

    rv = client.get("/list/math/2018")
    assert rv.status_code == 200

    rv = client.get("/list/math/2020")  
    assert rv.status_code == 200

    rv = client.get("/list/math/2001-01")
    assert rv.status_code == 200

def test_basic_lists_errors(client_with_fake_listings):
    client = client_with_fake_listings

    rv = client.get("/list/math/2090")  # year 2090, will need to revise after 2090
    assert rv.status_code == 404

    rv = client.get("/list/math/1980") #arxiv wasnt around yet 
    assert rv.status_code == 400

    rv = client.get("/list/math/80") #redirected to 2080 which is in future 
    assert rv.status_code == 404

    rv = client.get("/list/math/198") #nonsense year 
    assert rv.status_code == 400

    rv = client.get("/list/math/001") #no 3 digit years 
    assert rv.status_code == 400

    rv = client.get("/list/math/1")  #no 1 digit years
    assert rv.status_code == 400


def test_listing_authors(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01")
    assert rv.status_code == 200
    text = rv.data.decode("utf-8")
    au = "Eqab M. Rabei"
    assert au in text  # Simple check for author in response

    html = BeautifulSoup(text, "html.parser")

    auDivs = html.find_all("div", "list-authors")
    assert auDivs != None
    assert len(auDivs) > 5  # Should have some .list-author divs

    first_aus = auDivs[0].find_all("a")
    assert (
        len(first_aus) == 4
    )  # expect 4 <a> tags for first artcile "Fractional WKB Approximation"

    assert first_aus[0].get_text() == "Eqab M. Rabei"
    assert first_aus[1].get_text() == "Ibrahim M. A. Altarazi"
    assert first_aus[2].get_text() == "Sami I. Muslih"
    assert first_aus[3].get_text() == "Dumitru Baleanu"

    assert (
        " ," not in auDivs[0].get_text()
    )  # Should not have a comma with a space in front of it


def test_paging_first(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01")
    assert rv.status_code == 200

    rvdata = rv.data.decode("utf-8")
    html = BeautifulSoup(rvdata, "html.parser")

    paging = html.find(id="dlpage").find_all("div", class_=lambda x: x and 'alert' not in x)[0]
    assert paging != None
    tgs = paging.find_all(["span", "a"])
    assert tgs != None
    assert len(tgs) == 6

    assert tgs[0].name == "span"
    assert tgs[0].get_text() == "1-50"

    assert tgs[1].name == "a"
    assert tgs[1].get_text() == "51-100"

    assert tgs[2].name == "a"
    assert tgs[2].get_text() == "101-150"

    assert tgs[3].name == "a"
    assert tgs[3].get_text() == "151-200"

    assert tgs[4].name == "span"
    assert tgs[4].get_text() == "..."

    assert tgs[5].name == "a"
    assert tgs[5].get_text() == "1001-1001"

    # find the first article index tag
    first_index_atag = (
        html.find(id="articles")
        .find_all("dt")[0]
        .find("a", string=re.compile(r"\[\d*\]"))
    )
    assert first_index_atag != None
    assert first_index_atag["name"] == "item1"
    assert first_index_atag.string == "[1]"


def test_paging_second(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?skip=25&show=25")
    assert rv.status_code == 200

    rvdata = rv.data.decode("utf-8")
    html = BeautifulSoup(rvdata, "html.parser")

    paging = html.find(id="dlpage").find_all("div", class_=lambda x: x and 'alert' not in x)[0]
    assert paging != None
    tgs = paging.find_all(["span", "a"])
    assert tgs != None
    assert len(tgs) == 7

    assert tgs[0].name == "a"
    assert tgs[0].get_text() == "1-25"

    assert tgs[1].name == "span"
    assert tgs[1].get_text() == "26-50"

    assert tgs[2].name == "a"
    assert tgs[2].get_text() == "51-75"

    assert tgs[3].name == "a"
    assert tgs[3].get_text() == "76-100"

    assert tgs[4].name == "a"
    assert tgs[4].get_text() == "101-125"

    assert tgs[5].name == "span"
    assert tgs[5].get_text() == "..."

    assert tgs[6].name == "a"
    assert tgs[6].get_text() == "1001-1001"

    # find the first article index tag
    first_index_atag = (
        html.find(id="articles")
        .find_all("dt")[0]
        .find("a", string=re.compile(r"\[\d*\]"))
    )
    assert first_index_atag != None
    assert first_index_atag["name"] != "item1"  # first item index should not be 1
    assert first_index_atag.string == "[26]"


def test_paging_middle(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?skip=175&show=25")
    assert rv.status_code == 200

    rvdata = rv.data.decode("utf-8")
    html = BeautifulSoup(rvdata, "html.parser")

    paging = html.find(id="dlpage").find_all("div", class_=lambda x: x and 'alert' not in x)[0]
    assert paging != None
    tgs = paging.find_all(["span", "a"])
    assert tgs != None
    assert len(tgs) == 11

    assert tgs[0].name == "a"
    assert tgs[0].get_text() == "1-25"

    assert tgs[1].name == "span"
    assert tgs[1].get_text() == "..."

    assert tgs[2].name == "a"
    assert tgs[2].get_text() == "101-125"

    assert tgs[3].name == "a"
    assert tgs[3].get_text() == "126-150"

    assert tgs[4].name == "a"
    assert tgs[4].get_text() == "151-175"

    assert tgs[5].name == "span"
    assert tgs[5].get_text() == "176-200"

    assert tgs[6].name == "a"
    assert tgs[6].get_text() == "201-225"

    assert tgs[7].name == "a"
    assert tgs[7].get_text() == "226-250"

    assert tgs[8].name == "a"
    assert tgs[8].get_text() == "251-275"

    assert tgs[9].name == "span"
    assert tgs[9].get_text() == "..."

    assert tgs[10].name == "a"
    assert tgs[10].get_text() == "1001-1001"

    # find the first article index tag
    first_index_atag = (
        html.find(id="articles")
        .find_all("dt")[0]
        .find("a", string=re.compile(r"\[\d*\]"))
    )
    assert first_index_atag != None
    assert first_index_atag["name"] != "item1"  # 'first item index should not be 1'
    assert first_index_atag.string == "[176]"


def test_paging_last(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?skip=1000&show=25")
    assert rv.status_code == 200

    rvdata = rv.data.decode("utf-8")
    html = BeautifulSoup(rvdata, "html.parser")

    paging = html.find(id="dlpage").find_all("div", class_=lambda x: x and 'alert' not in x)[0]
    assert paging != None
    tgs = paging.find_all(["span", "a"])
    assert tgs and len(tgs) == 6

    assert tgs[0].name == "a"
    assert tgs[0].get_text() == "1-25"

    assert tgs[1].name == "span"
    assert tgs[1].get_text() == "..."

    assert tgs[2].name == "a"
    assert tgs[2].get_text() == "926-950"

    assert tgs[3].name == "a"
    assert tgs[3].get_text() == "951-975"

    assert tgs[4].name == "a"
    assert tgs[4].get_text() == "976-1000"

    assert tgs[5].name == "span"
    assert tgs[5].get_text() == "1001-1001"

    # find the first article index tag
    first_index_atag = (
        html.find(id="articles")
        .find_all("dt")[0]
        .find("a", string=re.compile(r"\[\d*\]"))
    )
    assert first_index_atag != None
    assert first_index_atag["name"] != "item1"  # 'first item index should not be 1'
    assert first_index_atag.string == "[1001]"


def test_paging_penultimate(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?skip=975&show=25")
    assert rv.status_code == 200

    rvdata = rv.data.decode("utf-8")
    html = BeautifulSoup(rvdata, "html.parser")

    paging = html.find(id="dlpage").find_all("div", class_=lambda x: x and 'alert' not in x)[0]
    assert paging != None
    tgs = paging.find_all(["span", "a"])
    assert tgs != None
    assert len(tgs) == 7

    assert tgs[0].name == "a"
    assert tgs[0].get_text() == "1-25"

    assert tgs[1].name == "span"
    assert tgs[1].get_text() == "..."

    assert tgs[2].name == "a"
    assert tgs[2].get_text() == "901-925"

    assert tgs[3].name == "a"
    assert tgs[3].get_text() == "926-950"

    assert tgs[4].name == "a"
    assert tgs[4].get_text() == "951-975"

    assert tgs[5].name == "span"
    assert tgs[5].get_text() == "976-1000"

    assert tgs[6].name == "a"
    assert tgs[6].get_text() == "1001-1001"

    # find the first article index tag
    first_index_atag = (
        html.find(id="articles")
        .find_all("dt")[0]
        .find("a", string=re.compile(r"\[\d*\]"))
    )
    assert first_index_atag != None
    assert first_index_atag["name"] != "item1"  # 'first item index should not be 1'
    assert first_index_atag.string == "[976]"


def test_paging_925(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?skip=925&show=25")
    assert rv.status_code == 200

    rvdata = rv.data.decode("utf-8")
    html = BeautifulSoup(rvdata, "html.parser")

    paging = html.find(id="dlpage").find_all("div", class_=lambda x: x and 'alert' not in x)[0]
    assert paging != None
    tgs = paging.find_all(["span", "a"])
    assert tgs and len(tgs) == 9

    assert tgs[0].name == "a"
    assert tgs[0].get_text() == "1-25"

    assert tgs[1].name == "span"
    assert tgs[1].get_text() == "..."

    assert tgs[2].name == "a"
    assert tgs[2].get_text() == "851-875"

    assert tgs[3].name == "a"
    assert tgs[3].get_text() == "876-900"

    assert tgs[4].name == "a"
    assert tgs[4].get_text() == "901-925"

    assert tgs[5].name == "span"
    assert tgs[5].get_text() == "926-950"

    assert tgs[6].name == "a"
    assert tgs[6].get_text() == "951-975"

    assert tgs[7].name == "a"
    assert tgs[7].get_text() == "976-1000"

    assert tgs[8].name == "a"
    assert tgs[8].get_text() == "1001-1001"

    # find the first article index tag
    first_index_atag = (
        html.find(id="articles")
        .find_all("dt")[0]
        .find("a", string=re.compile(r"\[\d*\]"))
    )
    assert first_index_atag != None
    assert first_index_atag["name"] != "item1"  # 'first item index should not be 1'
    assert first_index_atag.string == "[926]"

def test_paging_all(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?show=25")
    assert 'show=2000rel="nofollow">all</a>' in rv.text.replace('\n', '').replace(' ', '')

    rv = client.get("/list/hep-ph/2009-01?show=2000")
    assert 'show=2000rel="nofollow">all</a>' not in rv.text.replace('\n', '').replace(' ', '')


def test_odd_requests(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/hep-ph/2009-01?skip=925&show=1000000")
    assert rv.status_code == 200

    rv = client.get("/list/hep-ph/bogusTimePeriod")
    assert rv.status_code != 200

    rv = client.get("/list/junkarchive")
    assert rv.status_code != 200

    rv = client.get("/list/ao-si/2009-01?skip=925&show=25")
    assert rv.status_code != 200

    rv = client.get("/list/math/2001-00")
    assert rv.status_code != 200

    rv = client.get("/list/math/2001-13")
    assert rv.status_code != 200

    rv = client.get("/list/math/2001-99")
    assert rv.status_code != 200

    rv = client.get("/list/math/2")
    assert rv.status_code != 200

    rv = client.get("/list/math/2001-999999")
    assert rv.status_code != 200


def test_not_modified_from_listing_service(client_with_fake_listings):
    client = client_with_fake_listings

    flservice = get_listing_service()
    flservice.list_new_articles = MagicMock(
        return_value=NotModifiedResponse(True, "Wed, 21 Oct 2015 07:28:00 GMT")
    )
    rv = client.get("/list/hep-ph/new")
    assert (
        rv.status_code == 304
    )  # /list controller should return 304 when service indicates not-modified

    flservice.list_pastweek_articles = MagicMock(
        return_value=NotModifiedResponse(True, "Wed, 21 Oct 2015 07:28:00 GMT")
    )
    rv = client.get("/list/hep-ph/recent")
    assert (
        rv.status_code == 304
    )  # '/list controller should return 304 when service indicates not-modified'
    rv = client.get("/list/hep-ph/pastweek")
    assert (
        rv.status_code == 304
    )  # '/list controller should return 304 when service indicates not-modified'

    flservice.list_articles_by_month = MagicMock(
        return_value=NotModifiedResponse(True, "Wed, 21 Oct 2015 07:28:00 GMT")
    )
    rv = client.get("/list/hep-ph/2018-01")
    assert (
        rv.status_code == 304
    )  # '/list controller should return 304 when service indicates not-modified'

    flservice.list_articles_by_year = MagicMock(
        return_value=NotModifiedResponse(True, "Wed, 21 Oct 2015 07:28:00 GMT")
    )
    rv = client.get("/list/hep-ph/2018")
    assert (
        rv.status_code == 304
    )  # '/list controller should return 304 when service indicates not-modified'


def test_list_called_from_archive(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get("/list/?archive=hep-ph&year=2008&month=03&submit=Go")
    assert rv.status_code == 200

    rv = client.get("/list/?archive=hep-ph&year=2008&month=all&submit=Go")
    assert rv.status_code == 200



def test_astro_ph_months(client_with_test_fs, abs_path):
    client = client_with_test_fs
    files = list( (abs_path / "ftp/astro-ph/listings").glob("./[0-9]*") )
    for file in files:
        year=int(file.stem[0:2])+1900
        if year< 1990:
            year+=100
        month=file.stem[2:4]
        name=f"{year}-{month}"
        rv = client.get(f"/list/astro-ph/{name}")
        assert rv.status_code == 200


def test_astro_ph_years(client_with_test_fs, abs_path):
    client = client_with_test_fs
    years=['1999', '1998', '1997', '1996','1995','1994','1993','2007']
    for yyyy in sorted(years):
        rv = client.get(f"/year/astro-ph/{yyyy}")
        assert rv.status_code == 200

    # start year with only partal data
    rv = client.get("/year/astro-ph/1992")
    assert rv.status_code == 200

    # 2023 only has start of the year and simulates a archive that stopped midyear
    rv = client.get("/year/astro-ph/2023")
    assert rv.status_code == 200


def test_astro_ph_ep_recent(client_with_test_fs):
    pytest.skip('fs_listing system doesnt do recent properly')
    client = client_with_test_fs
    rv = client.get(f"/list/astro-ph.EP/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "Earth and Planetary Astrophysics" in text
    assert "Authors and titles for recent submissions" in text

    assert "arXiv:2303.01496" in text
    assert "arXiv:2303.01458" in text
    assert "arXiv:2303.01358" in text
    assert "arXiv:2303.01337" in text
    assert "arXiv:2303.00867" in text
    assert "arXiv:2303.00768" in text
    assert "arXiv:2303.01154" in text
    assert "arXiv:2303.01138" in text
    assert "arXiv:2303.01100" in text
    assert "arXiv:2303.00812" in text
    assert "arXiv:2303.00670" in text
    assert "arXiv:2303.00659" in text
    assert "arXiv:2303.00624" in text
    assert "arXiv:2303.00540" in text
    assert "arXiv:2303.00397" in text
    assert "arXiv:2303.00221" in text
    assert "arXiv:2303.00084" in text
    assert "arXiv:2303.00062" in text
    assert "arXiv:2303.00012" in text
    assert "arXiv:2303.00011" in text
    assert "arXiv:2303.00006" in text
    assert "arXiv:2303.00718" in text
    assert "arXiv:2303.00063" in text
    assert "arXiv:2302.14847" in text
    assert "arXiv:2302.14425" in text

    rv = client.get("/list/astro-ph.EP/recent?skip=25&show=25")
    text = rv.text
    assert "arXiv:2302.14100" in text
    assert "arXiv:2302.14832" in text
    assert "arXiv:2302.14636" in text
    assert "arXiv:2302.14054" in text
    assert "arXiv:2302.13969" in text
    assert "arXiv:2302.13620" in text
    assert "arXiv:2302.13544" in text
    assert "arXiv:2302.13370" in text
    assert "arXiv:2302.13303" in text
    assert "arXiv:2302.13226" in text
    assert "arXiv:2302.12841" in text
    assert "arXiv:2302.13354" in text
    assert "arXiv:2302.12778" in text
    assert "arXiv:2302.12753" in text
    assert "arXiv:2302.12722" in text
    assert "arXiv:2302.12607" in text
    assert "arXiv:2302.12556" in text
    assert "arXiv:2302.12518" in text
    assert "arXiv:2302.12457" in text
    assert "arXiv:2302.12376" in text
    assert "arXiv:2302.12340" in text
    assert "arXiv:2302.12824" in text
    assert "arXiv:2302.12723" in text
    assert "arXiv:2302.12566" in text

    assert "49 entries" in text

def test_astro_ph_recent(client_with_test_fs):
    client = client_with_test_fs
    rv = client.get(f"/list/astro-ph/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "Total of 320 entries :" in text
    assert "Thu, 2 Mar 2023 (showing first 50 of 57 entries )" in text

    client = client_with_test_fs
    rv = client.get(f"/list/astro-ph.CO/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "63 entries" in text

    client = client_with_test_fs
    rv = client.get(f"/list/astro-ph.GA/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "101 entries" in text

    rv = client.get(f"/list/astro-ph.HE/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "85 entries" in text

    rv = client.get(f"/list/astro-ph.IM/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "55 entries" in text

    rv = client.get(f"/list/astro-ph.SR/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Fri, 3 Mar 2023" in text
    assert "67 entries" in text


def test_abs_in_new_listing(client_with_test_fs):
    """/list/new should have the abstracts"""
    client = client_with_test_fs
    rv = client.get("/list/astro-ph/new")
    assert rv.status_code == 200
    text = rv.text
    assert "We present a search for gas-containing dwarf galaxies" in text
    assert "is likely at play." in text
    # Test that cruft at end of abstract is not displayed
    assert "https://arxiv.org/abs/2303.00763" not in text
    assert "3197kb" not in text


def test_math_ph_9701(client_with_test_fs):
    client = client_with_test_fs
    rv = client.get("/list/math-ph/1997-01")
    assert rv.status_code == 200
    text = rv.text
    assert "On Exact Solutions" in text
    assert "unknown-id" not in text

def test_invalid_archive_years(client_with_test_fs):
    client = client_with_test_fs

    #started in 1996
    rv = client.get("/year/physics/1994")
    assert rv.status_code == 400
    text=rv.text
    assert 'Invalid year' in text

    #ended in 1997
    rv = client.get("/year/funct-an/1998")
    assert rv.status_code == 400
    text=rv.text
    assert 'Invalid year' in text
    

def test_year_archive_with_end_date(client_with_test_fs):
    client = client_with_test_fs
    rv = client.get("/year/funct-an/1996")
    assert rv.status_code == 200
    text=rv.text
    assert '<a href="/year/funct-an/1997">1997</a>' in text
    assert '<a href="/year/funct-an/1998">1998</a>' not in text

def test_listing_page_subsumed_archive( client_with_test_fs):
    client = client_with_test_fs
    rv = client.get("/list/alg-geom/new")
    assert rv.status_code == 200
    text = rv.text
    assert "Algebraic Geometry" in text
    assert "math.AG" in text
    rv = client.get("/list/alg-geom/recent")
    assert rv.status_code == 200
    text = rv.text
    assert "Algebraic Geometry" in text
    assert "math.AG" in text
    rv = client.get("/list/alg-geom/2021-03")
    assert rv.status_code == 200
    text = rv.text
    assert "Algebraic Geometry" in text
    assert "math.AG" in text

def test_YY_redirect(client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math-ph/03", follow_redirects=False)
    assert rv.status_code == 301
    assert rv.headers["Location"]== "/list/math-ph/2003"

    rv = client.get("/list/math-ph/03", follow_redirects=True)
    assert rv.status_code == 200
    assert "titles for 2003" in rv.text
    
def test_YYYYMM_redirect(client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math-ph/200301", follow_redirects=False)
    assert rv.status_code == 301
    assert rv.headers["Location"]== "/list/math-ph/2003-01"

    rv = client.get("/list/math-ph/200301", follow_redirects=True)
    assert rv.status_code == 200
    assert "titles for January 2003" in rv.text
    
# YYYY-M
def test_YYYY_M_redirect(client_with_db_listings):
    client = client_with_db_listings
    rv = client.get("/list/math-ph/2003-1", follow_redirects=False)
    assert rv.status_code == 301
    assert rv.headers["Location"]== "/list/math-ph/2003-01"

    rv = client.get("/list/math-ph/2003-1", follow_redirects=True)
    assert rv.status_code == 200
    assert "titles for January 2003" in rv.text

def test_basic_no_listings(client_with_db_listings):
    client = client_with_db_listings
    #month
    rv = client.get("/list/hep-lat/2024-01")
    assert rv.status_code == 200
    assert "No updates for this time period." in rv.text
    #year
    rv = client.get("/list/hep-lat/2024")
    assert rv.status_code == 200
    assert "No updates for this time period." in rv.text
    #current
    rv = client.get("/list/hep-lat/current")
    assert rv.status_code == 200
    assert "No updates for this time period." in rv.text

def test_no_listings_new(client_with_db_listings):
    client = client_with_db_listings
    #no updates at all
    rv = client.get("/list/hep-lat/new")
    assert rv.status_code == 200
    assert "No updates today." in rv.text

    #only some types of updates
    rv = client.get("/list/physics/new")
    assert rv.status_code == 200
    assert "No updates today." not in rv.text
    assert "Replacement submissions" in rv.text
    assert "New submissions" not in rv.text
    assert "Cross submissions" not in rv.text


#also tests sectioning visibility
@mock.patch.object(list_page, 'min_show', 1)
def test_no_listings_recent(client_with_db_listings):
    client = client_with_db_listings
    expected_string = "No updates for this time period."

    #no updates at all
    rv = client.get("/list/hep-lat/recent")
    assert rv.status_code == 200
    assert rv.text.count(expected_string) == 5
    assert rv.text.count("Thu, 3 Feb 2011") == 2
    assert rv.text.count("Wed, 2 Feb 2011") == 2
    assert rv.text.count("Tue, 1 Feb 2011") == 2
    assert rv.text.count("Mon, 31 Jan 2011") == 2
    assert rv.text.count("Fri, 28 Jan 2011") == 2

    #only some types of updates
    rv = client.get("/list/physics/recent")
    assert rv.status_code == 200
    assert rv.text.count(expected_string) == 4
    assert rv.text.count("Thu, 3 Feb 2011") == 2
    assert rv.text.count("Wed, 2 Feb 2011") == 2
    assert rv.text.count("Tue, 1 Feb 2011") == 2
    assert rv.text.count("Mon, 31 Jan 2011") == 2
    assert rv.text.count("Fri, 28 Jan 2011") == 2

    #skipped updates not shown
    rv = client.get("/list/physics/recent?skip=1")
    assert rv.status_code == 200
    assert rv.text.count(expected_string) == 2
    assert rv.text.count("Thu, 3 Feb 2011") == 1
    assert rv.text.count("Wed, 2 Feb 2011") == 1
    assert rv.text.count("Tue, 1 Feb 2011") == 1
    assert rv.text.count("Mon, 31 Jan 2011") == 2
    assert rv.text.count("Fri, 28 Jan 2011") == 2

    #sections farther ahead not shown
    rv = client.get("/list/physics/recent?show=1")
    assert rv.status_code == 200
    assert rv.text.count(expected_string) == 2
    assert rv.text.count("Thu, 3 Feb 2011") == 2
    assert rv.text.count("Wed, 2 Feb 2011") == 2
    assert rv.text.count("Tue, 1 Feb 2011") == 2
    assert rv.text.count("Mon, 31 Jan 2011") == 1
    assert rv.text.count("Fri, 28 Jan 2011") == 1

    #empty sections shown after a skip
    rv = client.get("/list/math/recent?skip=4")
    assert rv.status_code == 200
    assert rv.text.count(expected_string) == 1
    assert rv.text.count("Thu, 3 Feb 2011") == 1
    assert rv.text.count("Wed, 2 Feb 2011") == 1
    assert rv.text.count("Tue, 1 Feb 2011") == 1
    assert rv.text.count("Mon, 31 Jan 2011") == 2
    assert rv.text.count("Fri, 28 Jan 2011") == 2


def test_surrogate_keys(client_with_db_listings):
    client=client_with_db_listings

    rv = client.get("/list/math/recent?skip=4")
    head=rv.headers["Surrogate-Key"]
    assert " list " in " "+head+" "
    assert "list-recent" in head
    assert "announce" in head
    assert "list-recent-math" in head

    rv = client.get("/list/cs.SY/new")
    head=rv.headers["Surrogate-Key"]
    assert " list " in " "+head+" "
    assert "list-new" in head
    assert "announce" in head
    assert "list-new-eess.SY" in head
    
    rv = client.get("/list/solv-int/2005-06")
    head=rv.headers["Surrogate-Key"]
    assert " list " in " "+head+" "
    assert "list-ym" in head
    assert "announce"  not in head
    assert "list-2005-06-nlin.SI" in head

    rv = client.get("/list/astro-ph/2005")
    head=rv.headers["Surrogate-Key"]
    assert " list " in " "+head+" "
    assert "list-ym" in head
    assert "announce"  not in head
    assert "list-2005-astro-ph" in head

    rv = client.get(f"/list/astro-ph/{date.today().year:04d}")
    head=rv.headers["Surrogate-Key"]
    assert " list " in " "+head+" "
    assert "list-ym" in head
    assert "announce" in head

    rv = client.get(f"/list/astro-ph/current")
    head=rv.headers["Surrogate-Key"]
    assert " list " in " "+head+" "
    assert "list-ym" in head
    assert "announce" in head

