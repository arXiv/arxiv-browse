import re
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from browse.services.listing import get_listing_service

from app import app
from browse.domain.license import ASSUMED_LICENSE_URI
from browse.services.listing import get_listing_service


def test_basic_lists(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/hep-ph/09')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/hep-ph/new')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/hep-ph/current')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/hep-ph/pastweek')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/hep-ph/recent')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/hep-ph/0901?skip=925&show=25')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/astro-ph/04')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/math/92')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None) != None

    rv = client.get('/list/math/9201')
    assert rv.status_code == 200

    rv = client.get('/list/math/0101')
    assert rv.status_code == 200

    rv = client.get('/list/math/0102')
    assert rv.status_code == 200

    rv = client.get('/list/math/0103')
    assert rv.status_code == 200

    rv = client.get('/list/math/0104')
    assert rv.status_code == 200

    rv = client.get('/list/math/0105')
    assert rv.status_code == 200

    rv = client.get('/list/math/0106')
    assert rv.status_code == 200

    rv = client.get('/list/math/0107')
    assert rv.status_code == 200

    rv = client.get('/list/math/0108')
    assert rv.status_code == 200

    rv = client.get('/list/math/0109')
    assert rv.status_code == 200

    rv = client.get('/list/math/0110')
    assert rv.status_code == 200

    rv = client.get('/list/math/0111')
    assert rv.status_code == 200

    rv = client.get('/list/math/0112')
    assert rv.status_code == 200

    rv = client.get('/list/math/01')
    assert rv.status_code == 200

    rv = client.get('/list/math/18')
    assert rv.status_code == 200

    rv = client.get('/list/math/20')  # year 2020
    assert rv.status_code == 200

    rv = client.get('/list/math/30')  # year 2030
    assert rv.status_code == 200

    rv = client.get('/list/math/200101')
    assert rv.status_code == 200

def test_listing_authors(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901')
    assert rv.status_code == 200
    text = rv.data.decode('utf-8')
    au = 'Eqab M. Rabei'
    assert au in text  # Simple check for author in response

    html = BeautifulSoup(text, 'html.parser')

    auDivs = html.find_all('div', 'list-authors')
    assert auDivs != None
    assert len(auDivs) > 5  #Should have some .list-author divs

    first_aus = auDivs[0].find_all('a')
    assert len(first_aus) == 4  # expect 4 <a> tags for first artcile "Fractional WKB Approximation"
    
    assert first_aus[0].get_text() == 'Eqab M. Rabei'
    assert first_aus[1].get_text() == 'Ibrahim M. A. Altarazi'
    assert first_aus[2].get_text() == 'Sami I. Muslih'
    assert first_aus[3].get_text() == 'Dumitru Baleanu'

    assert ' ,' not in auDivs[0].get_text()  # Should not have a comma with a space in front of it

def test_paging_first(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901')
    assert rv.status_code == 200

    rvdata = rv.data.decode('utf-8')
    html = BeautifulSoup(rvdata, 'html.parser')

    paging = html.find(id='dlpage').find_all('div')[0]
    assert paging != None
    tgs = paging.find_all(['span', 'a'])
    assert tgs != None
    assert len(tgs) == 6

    assert tgs[0].name  == 'span'
    assert tgs[0].get_text()  == '1-25'

    assert tgs[1].name  == 'a'
    assert tgs[1].get_text()  == '26-50'

    assert tgs[2].name  == 'a'
    assert tgs[2].get_text()  == '51-75'

    assert tgs[3].name  == 'a'
    assert tgs[3].get_text()  == '76-100'

    assert tgs[4].name  == 'span'
    assert tgs[4].get_text()  == '...'

    assert tgs[5].name  == 'a'
    assert tgs[5].get_text()  == '1001-1001'

    # find the first article index tag
    first_index_atag = html.find(id='articles').find_all(
        'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
    assert first_index_atag != None
    assert first_index_atag['name']  == 'item1'
    assert first_index_atag.string  == '[1]'

def test_paging_second(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901?skip=25&show=25')
    assert rv.status_code == 200

    rvdata = rv.data.decode('utf-8')
    html = BeautifulSoup(rvdata, 'html.parser')

    paging = html.find(id='dlpage').find_all('div')[0]
    assert paging != None
    tgs = paging.find_all(['span', 'a'])
    assert tgs != None
    assert len(tgs) == 7

    assert tgs[0].name  == 'a'
    assert tgs[0].get_text()  == '1-25'

    assert tgs[1].name  == 'span'
    assert tgs[1].get_text()  == '26-50'

    assert tgs[2].name  == 'a'
    assert tgs[2].get_text()  == '51-75'

    assert tgs[3].name  == 'a'
    assert tgs[3].get_text()  == '76-100'

    assert tgs[4].name  == 'a'
    assert tgs[4].get_text()  == '101-125'

    assert tgs[5].name  == 'span'
    assert tgs[5].get_text()  == '...'

    assert tgs[6].name  == 'a'
    assert tgs[6].get_text()  == '1001-1001'

    # find the first article index tag
    first_index_atag = html.find(id='articles').find_all(
        'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
    assert first_index_atag != None
    assert first_index_atag['name'] != 'item1'  # first item index should not be 1
    assert first_index_atag.string  == '[26]'

def test_paging_middle(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901?skip=175&show=25')
    assert rv.status_code == 200

    rvdata = rv.data.decode('utf-8')
    html = BeautifulSoup(rvdata, 'html.parser')

    paging = html.find(id='dlpage').find_all('div')[0]
    assert paging != None
    tgs = paging.find_all(['span', 'a'])
    assert tgs != None
    assert len(tgs) == 11

    assert tgs[0].name  == 'a'
    assert tgs[0].get_text()  == '1-25'

    assert tgs[1].name  == 'span'
    assert tgs[1].get_text()  == '...'

    assert tgs[2].name  == 'a'
    assert tgs[2].get_text()  == '101-125'

    assert tgs[3].name  == 'a'
    assert tgs[3].get_text()  == '126-150'

    assert tgs[4].name  == 'a'
    assert tgs[4].get_text()  == '151-175'

    assert tgs[5].name  == 'span'
    assert tgs[5].get_text()  == '176-200'

    assert tgs[6].name  == 'a'
    assert tgs[6].get_text()  == '201-225'

    assert tgs[7].name  == 'a'
    assert tgs[7].get_text()  == '226-250'

    assert tgs[8].name  == 'a'
    assert tgs[8].get_text()  == '251-275'

    assert tgs[9].name  == 'span'
    assert tgs[9].get_text()  == '...'

    assert tgs[10].name  == 'a'
    assert tgs[10].get_text()  == '1001-1001'

    # find the first article index tag
    first_index_atag = html.find(id='articles').find_all(
        'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
    assert first_index_atag != None
    assert first_index_atag['name'] != 'item1'  # 'first item index should not be 1'
    assert first_index_atag.string  == '[176]'

def test_paging_last(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901?skip=1000&show=25')
    assert rv.status_code == 200

    rvdata = rv.data.decode('utf-8')
    html = BeautifulSoup(rvdata, 'html.parser')

    paging = html.find(id='dlpage').find_all('div')[0]
    assert paging != None
    tgs = paging.find_all(['span', 'a'])
    assert tgs and len(tgs) == 6

    assert tgs[0].name  == 'a'
    assert tgs[0].get_text()  == '1-25'

    assert tgs[1].name  == 'span'
    assert tgs[1].get_text()  == '...'

    assert tgs[2].name  == 'a'
    assert tgs[2].get_text()  == '926-950'

    assert tgs[3].name  == 'a'
    assert tgs[3].get_text()  == '951-975'

    assert tgs[4].name  == 'a'
    assert tgs[4].get_text()  == '976-1000'

    assert tgs[5].name  == 'span'
    assert tgs[5].get_text()  == '1001-1001'

    # find the first article index tag
    first_index_atag = html.find(id='articles').find_all(
        'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
    assert first_index_atag != None
    assert first_index_atag['name'] != 'item1'  # 'first item index should not be 1'
    assert first_index_atag.string  == '[1001]'

def test_paging_penultimate(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901?skip=975&show=25')
    assert rv.status_code == 200

    rvdata = rv.data.decode('utf-8')
    html = BeautifulSoup(rvdata, 'html.parser')

    paging = html.find(id='dlpage').find_all('div')[0]
    assert paging != None
    tgs = paging.find_all(['span', 'a'])
    assert tgs != None
    assert len(tgs) == 7

    assert tgs[0].name  == 'a'
    assert tgs[0].get_text()  == '1-25'

    assert tgs[1].name  == 'span'
    assert tgs[1].get_text()  == '...'

    assert tgs[2].name  == 'a'
    assert tgs[2].get_text()  == '901-925'

    assert tgs[3].name  == 'a'
    assert tgs[3].get_text()  == '926-950'

    assert tgs[4].name  == 'a'
    assert tgs[4].get_text()  == '951-975'

    assert tgs[5].name  == 'span'
    assert tgs[5].get_text()  == '976-1000'

    assert tgs[6].name  == 'a'
    assert tgs[6].get_text()  == '1001-1001'

    # find the first article index tag
    first_index_atag = html.find(id='articles').find_all(
        'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
    assert first_index_atag != None
    assert first_index_atag['name'] != 'item1'  # 'first item index should not be 1'
    assert first_index_atag.string  == '[976]'

def test_paging_925(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901?skip=925&show=25')
    assert rv.status_code == 200

    rvdata = rv.data.decode('utf-8')
    html = BeautifulSoup(rvdata, 'html.parser')

    paging = html.find(id='dlpage').find_all('div')[0]
    assert paging != None
    tgs = paging.find_all(['span', 'a'])
    assert tgs and len(tgs) == 9

    assert tgs[0].name  == 'a'
    assert tgs[0].get_text()  == '1-25'

    assert tgs[1].name  == 'span'
    assert tgs[1].get_text()  == '...'

    assert tgs[2].name  == 'a'
    assert tgs[2].get_text()  == '851-875'

    assert tgs[3].name  == 'a'
    assert tgs[3].get_text()  == '876-900'

    assert tgs[4].name  == 'a'
    assert tgs[4].get_text()  == '901-925'

    assert tgs[5].name  == 'span'
    assert tgs[5].get_text()  == '926-950'

    assert tgs[6].name  == 'a'
    assert tgs[6].get_text()  == '951-975'

    assert tgs[7].name  == 'a'
    assert tgs[7].get_text()  == '976-1000'

    assert tgs[8].name  == 'a'
    assert tgs[8].get_text()  == '1001-1001'

    # find the first article index tag
    first_index_atag = html.find(id='articles').find_all(
        'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
    assert first_index_atag != None
    assert first_index_atag['name'] != 'item1'  # 'first item index should not be 1'
    assert first_index_atag.string  == '[926]'

def test_odd_requests(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/hep-ph/0901?skip=925&show=1000000')
    assert rv.status_code == 200

    rv = client.get('/list/hep-ph/bogusTimePeriod')
    assert rv.status_code != 200

    rv = client.get('/list/junkarchive')
    assert rv.status_code != 200

    rv = client.get('/list/ao-si/0901?skip=925&show=25')
    assert rv.status_code != 200

    rv = client.get('/list/math/0100')
    assert rv.status_code != 200

    rv = client.get('/list/math/0113')
    assert rv.status_code != 200

    rv = client.get('/list/math/0199')
    assert rv.status_code != 200

    rv = client.get('/list/math/200199')
    assert rv.status_code != 200

    rv = client.get('/list/math/2')
    assert rv.status_code != 200

    rv = client.get('/list/math/2001999999')
    assert rv.status_code != 200

def test_not_modified_from_listing_service(client_with_fake_listings):
    client = client_with_fake_listings

    flservice = get_listing_service()
    flservice.list_new_articles = MagicMock(return_value={'not_modified': True,
                                                          'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
    rv = client.get('/list/hep-ph/new')
    assert rv.status_code == 304  # /list controller should return 304 when service indicates not-modified

    flservice.list_pastweek_articles = MagicMock(return_value={'not_modified': True,
                                                               'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
    rv = client.get('/list/hep-ph/recent')
    assert rv.status_code == 304  # '/list controller should return 304 when service indicates not-modified'        
    rv = client.get('/list/hep-ph/pastweek')
    assert rv.status_code == 304  # '/list controller should return 304 when service indicates not-modified'

    flservice.list_articles_by_month = MagicMock(return_value={'not_modified': True,
                                                               'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
    rv = client.get('/list/hep-ph/1801')
    assert rv.status_code == 304  # '/list controller should return 304 when service indicates not-modified'

    flservice.list_articles_by_year = MagicMock(return_value={'not_modified': True,
                                                              'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
    rv = client.get('/list/hep-ph/18')
    assert rv.status_code == 304  # '/list controller should return 304 when service indicates not-modified'

def test_list_called_from_archive(client_with_fake_listings):
    client = client_with_fake_listings
    rv = client.get('/list/?archive=hep-ph&year=08&month=03&submit=Go')        
    assert rv.status_code == 200

    rv = client.get('/list/?archive=hep-ph&year=08&month=all&submit=Go')        
    assert rv.status_code == 200
