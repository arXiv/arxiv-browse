import unittest
import pytest
import re
from hamcrest import *
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from tests.test_fs_abs_parser import ABS_FILES
from browse.services.documents.fs_implementation.parse_abs import parse_abs_file
from browse.domain.license import ASSUMED_LICENSE_URI
from browse.services.listing.fake_listings import FakeListingFilesService
from browse.services.listing import ListingService, get_listing_service
import os



def test_basic_db_lists(dbclient):
    rv = dbclient.get('/list/hep-ph/1102')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None)

    
def test_basic_lists(client_with_fake_listings):
    rv = client_with_fake_listings.get('/list/hep-ph/0901')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None)


# def test_basic_lists(client_with_fake_listings):
#     rv = client_with_fake_listings.get('/list/hep-ph/0901')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/hep-ph/09')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/hep-ph/new')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/hep-ph/current')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/hep-ph/pastweek')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/hep-ph/recent')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/hep-ph/0901?skip=925&show=25')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/astro-ph/04')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/math/92')
#     assertEqual(rv.status_code, 200)
#     assertNotEqual(rv.headers.get('Expires', None), None)

#     rv = client_with_fake_listings.get('/list/math/9201')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0101')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0102')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0103')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0104')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0105')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0106')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0107')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0108')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0109')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0110')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0111')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/0112')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/01')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/18')
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/20')  # year 2020
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/30')  # year 2030
#     assertEqual(rv.status_code, 200)

#     rv = client_with_fake_listings.get('/list/math/200101')
#     assertEqual(rv.status_code, 200)

# @pytest.mark.usefixtures('client_with_fake_listings')
# class ListPageTest(unittest.TestCase):
        

#     def test_listing_authors(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901')
#         self.assertEqual(rv.status_code, 200)
#         au = b'Eqab M. Rabei'
#         assert au in rv.data, f'Simple check for author {au} in response.'

#         html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

#         auDivs = html.find_all('div', 'list-authors')
#         assert_that(auDivs, not_none())
#         assert_that(len(auDivs), greater_than(
#             5), 'Should have some .list-author divs')

#         first_aus = auDivs[0].find_all('a')
#         assert_that(first_aus, has_length(4),
#                     'expect 4 <a> tags for first artcile "Fractional WKB Approximation"')

#         assert_that(first_aus[0].get_text(), equal_to('Eqab M. Rabei'))
#         assert_that(first_aus[1].get_text(),
#                     equal_to('Ibrahim M. A. Altarazi'))
#         assert_that(first_aus[2].get_text(), equal_to('Sami I. Muslih'))
#         assert_that(first_aus[3].get_text(), equal_to('Dumitru Baleanu'))

#         assert_that(auDivs[0].get_text(), is_not(contains_string(' ,')),
#                     'Should not have a comma with a space in front of it')

#     def test_paging_first(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901')
#         self.assertEqual(rv.status_code, 200)

#         rvdata = rv.data.decode('utf-8')
#         html = BeautifulSoup(rvdata, 'html.parser')

#         paging = html.find(id='dlpage').find_all('div')[0]
#         assert_that(paging, not_none())
#         tgs = paging.find_all(['span', 'a'])
#         assert_that(tgs, not_none())
#         assert_that(len(tgs), 6)

#         assert_that(tgs[0].name, equal_to('span'))
#         assert_that(tgs[0].get_text(), equal_to('1-25'))

#         assert_that(tgs[1].name, equal_to('a'))
#         assert_that(tgs[1].get_text(), equal_to('26-50'))

#         assert_that(tgs[2].name, equal_to('a'))
#         assert_that(tgs[2].get_text(), equal_to('51-75'))

#         assert_that(tgs[3].name, equal_to('a'))
#         assert_that(tgs[3].get_text(), equal_to('76-100'))

#         assert_that(tgs[4].name, equal_to('span'))
#         assert_that(tgs[4].get_text(), equal_to('...'))

#         assert_that(tgs[5].name, equal_to('a'))
#         assert_that(tgs[5].get_text(), equal_to('1001-1001'))

#         # find the first article index tag
#         first_index_atag = html.find(id='articles').find_all(
#             'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
#         assert_that(first_index_atag, not_none())
#         assert_that(first_index_atag['name'], equal_to('item1'))
#         assert_that(first_index_atag.string, equal_to('[1]'))

#     def test_paging_second(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901?skip=25&show=25')
#         self.assertEqual(rv.status_code, 200)

#         rvdata = rv.data.decode('utf-8')
#         html = BeautifulSoup(rvdata, 'html.parser')

#         paging = html.find(id='dlpage').find_all('div')[0]
#         assert_that(paging, not_none())
#         tgs = paging.find_all(['span', 'a'])
#         assert_that(tgs, not_none())
#         assert_that(len(tgs), 7)

#         assert_that(tgs[0].name, equal_to('a'))
#         assert_that(tgs[0].get_text(), equal_to('1-25'))

#         assert_that(tgs[1].name, equal_to('span'))
#         assert_that(tgs[1].get_text(), equal_to('26-50'))

#         assert_that(tgs[2].name, equal_to('a'))
#         assert_that(tgs[2].get_text(), equal_to('51-75'))

#         assert_that(tgs[3].name, equal_to('a'))
#         assert_that(tgs[3].get_text(), equal_to('76-100'))

#         assert_that(tgs[4].name, equal_to('a'))
#         assert_that(tgs[4].get_text(), equal_to('101-125'))

#         assert_that(tgs[5].name, equal_to('span'))
#         assert_that(tgs[5].get_text(), equal_to('...'))

#         assert_that(tgs[6].name, equal_to('a'))
#         assert_that(tgs[6].get_text(), equal_to('1001-1001'))

#         # find the first article index tag
#         first_index_atag = html.find(id='articles').find_all(
#             'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
#         assert_that(first_index_atag, not_none())
#         assert_that(first_index_atag['name'], is_not(
#             'item1'), 'first item index should not be 1')
#         assert_that(first_index_atag.string, equal_to('[26]'))

#     def test_paging_middle(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901?skip=175&show=25')
#         self.assertEqual(rv.status_code, 200)

#         rvdata = rv.data.decode('utf-8')
#         html = BeautifulSoup(rvdata, 'html.parser')

#         paging = html.find(id='dlpage').find_all('div')[0]
#         assert_that(paging, not_none())
#         tgs = paging.find_all(['span', 'a'])
#         assert_that(tgs, not_none())
#         assert_that(len(tgs), 7)

#         assert_that(tgs[0].name, equal_to('a'))
#         assert_that(tgs[0].get_text(), equal_to('1-25'))

#         assert_that(tgs[1].name, equal_to('span'))
#         assert_that(tgs[1].get_text(), equal_to('...'))

#         assert_that(tgs[2].name, equal_to('a'))
#         assert_that(tgs[2].get_text(), equal_to('101-125'))

#         assert_that(tgs[3].name, equal_to('a'))
#         assert_that(tgs[3].get_text(), equal_to('126-150'))

#         assert_that(tgs[4].name, equal_to('a'))
#         assert_that(tgs[4].get_text(), equal_to('151-175'))

#         assert_that(tgs[5].name, equal_to('span'))
#         assert_that(tgs[5].get_text(), equal_to('176-200'))

#         assert_that(tgs[6].name, equal_to('a'))
#         assert_that(tgs[6].get_text(), equal_to('201-225'))

#         assert_that(tgs[7].name, equal_to('a'))
#         assert_that(tgs[7].get_text(), equal_to('226-250'))

#         assert_that(tgs[8].name, equal_to('a'))
#         assert_that(tgs[8].get_text(), equal_to('251-275'))

#         assert_that(tgs[9].name, equal_to('span'))
#         assert_that(tgs[9].get_text(), equal_to('...'))

#         assert_that(tgs[10].name, equal_to('a'))
#         assert_that(tgs[10].get_text(), equal_to('1001-1001'))

#         # find the first article index tag
#         first_index_atag = html.find(id='articles').find_all(
#             'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
#         assert_that(first_index_atag, not_none())
#         assert_that(first_index_atag['name'], is_not(
#             'item1'), 'first item index should not be 1')
#         assert_that(first_index_atag.string, equal_to('[176]'))

#     def test_paging_last(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901?skip=1000&show=25')
#         self.assertEqual(rv.status_code, 200)

#         rvdata = rv.data.decode('utf-8')
#         html = BeautifulSoup(rvdata, 'html.parser')

#         paging = html.find(id='dlpage').find_all('div')[0]
#         assert_that(paging, not_none())
#         tgs = paging.find_all(['span', 'a'])
#         assert_that(tgs, not_none())
#         assert_that(len(tgs), 7)

#         assert_that(tgs[0].name, equal_to('a'))
#         assert_that(tgs[0].get_text(), equal_to('1-25'))

#         assert_that(tgs[1].name, equal_to('span'))
#         assert_that(tgs[1].get_text(), equal_to('...'))

#         assert_that(tgs[2].name, equal_to('a'))
#         assert_that(tgs[2].get_text(), equal_to('926-950'))

#         assert_that(tgs[3].name, equal_to('a'))
#         assert_that(tgs[3].get_text(), equal_to('951-975'))

#         assert_that(tgs[4].name, equal_to('a'))
#         assert_that(tgs[4].get_text(), equal_to('976-1000'))

#         assert_that(tgs[5].name, equal_to('span'))
#         assert_that(tgs[5].get_text(), equal_to('1001-1001'))

#         # find the first article index tag
#         first_index_atag = html.find(id='articles').find_all(
#             'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
#         assert_that(first_index_atag, not_none())
#         assert_that(first_index_atag['name'], is_not(
#             'item1'), 'first item index should not be 1')
#         assert_that(first_index_atag.string, equal_to('[1001]'))

#     def test_paging_penultimate(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901?skip=975&show=25')
#         self.assertEqual(rv.status_code, 200)

#         rvdata = rv.data.decode('utf-8')
#         html = BeautifulSoup(rvdata, 'html.parser')

#         paging = html.find(id='dlpage').find_all('div')[0]
#         assert_that(paging, not_none())
#         tgs = paging.find_all(['span', 'a'])
#         assert_that(tgs, not_none())
#         assert_that(len(tgs), 7)

#         assert_that(tgs[0].name, equal_to('a'))
#         assert_that(tgs[0].get_text(), equal_to('1-25'))

#         assert_that(tgs[1].name, equal_to('span'))
#         assert_that(tgs[1].get_text(), equal_to('...'))

#         assert_that(tgs[2].name, equal_to('a'))
#         assert_that(tgs[2].get_text(), equal_to('901-925'))

#         assert_that(tgs[3].name, equal_to('a'))
#         assert_that(tgs[3].get_text(), equal_to('926-950'))

#         assert_that(tgs[4].name, equal_to('a'))
#         assert_that(tgs[4].get_text(), equal_to('951-975'))

#         assert_that(tgs[5].name, equal_to('span'))
#         assert_that(tgs[5].get_text(), equal_to('976-1000'))

#         assert_that(tgs[6].name, equal_to('a'))
#         assert_that(tgs[6].get_text(), equal_to('1001-1001'))

#         # find the first article index tag
#         first_index_atag = html.find(id='articles').find_all(
#             'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
#         assert_that(first_index_atag, not_none())
#         assert_that(first_index_atag['name'], is_not(
#             'item1'), 'first item index should not be 1')
#         assert_that(first_index_atag.string, equal_to('[976]'))

#     def test_paging_925(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901?skip=925&show=25')
#         self.assertEqual(rv.status_code, 200)

#         rvdata = rv.data.decode('utf-8')
#         html = BeautifulSoup(rvdata, 'html.parser')

#         paging = html.find(id='dlpage').find_all('div')[0]
#         assert_that(paging, not_none())
#         tgs = paging.find_all(['span', 'a'])
#         assert_that(tgs, not_none())
#         assert_that(len(tgs), 7)

#         assert_that(tgs[0].name, equal_to('a'))
#         assert_that(tgs[0].get_text(), equal_to('1-25'))

#         assert_that(tgs[1].name, equal_to('span'))
#         assert_that(tgs[1].get_text(), equal_to('...'))

#         assert_that(tgs[2].name, equal_to('a'))
#         assert_that(tgs[2].get_text(), equal_to('851-875'))

#         assert_that(tgs[3].name, equal_to('a'))
#         assert_that(tgs[3].get_text(), equal_to('876-900'))

#         assert_that(tgs[4].name, equal_to('a'))
#         assert_that(tgs[4].get_text(), equal_to('901-925'))

#         assert_that(tgs[5].name, equal_to('span'))
#         assert_that(tgs[5].get_text(), equal_to('926-950'))

#         assert_that(tgs[6].name, equal_to('a'))
#         assert_that(tgs[6].get_text(), equal_to('951-975'))

#         assert_that(tgs[7].name, equal_to('a'))
#         assert_that(tgs[7].get_text(), equal_to('976-1000'))

#         assert_that(tgs[8].name, equal_to('a'))
#         assert_that(tgs[8].get_text(), equal_to('1001-1001'))

#         # find the first article index tag
#         first_index_atag = html.find(id='articles').find_all(
#             'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
#         assert_that(first_index_atag, not_none())
#         assert_that(first_index_atag['name'], is_not(
#             'item1'), 'first item index should not be 1')
#         assert_that(first_index_atag.string, equal_to('[926]'))

#     def test_odd_requests(self):
#         rv = self.client_with_fake_listings.get('/list/hep-ph/0901?skip=925&show=1000000')
#         self.assertEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/hep-ph/bogusTimePeriod')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/junkarchive')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/ao-si/0901?skip=925&show=25')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/math/0100')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/math/0113')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/math/0199')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/math/200199')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/math/2')
#         self.assertNotEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/math/2001999999')
#         self.assertNotEqual(rv.status_code, 200)

#     def test_not_modified_from_listing_service(self):
#         with self.app.app_context():
#             flservice = get_listing_service()
#             flservice.list_new_articles = MagicMock(return_value={'not_modified': True,
#                                                                   'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
#             rv = self.client_with_fake_listings.get('/list/hep-ph/new')
#             self.assertEqual(
#                 rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')
            
#             flservice.list_pastweek_articles = MagicMock(return_value={'not_modified': True,
#                                                                        'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
#             rv = self.client_with_fake_listings.get('/list/hep-ph/recent')
#             self.assertEqual(
#                 rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')        
#             rv = self.client_with_fake_listings.get('/list/hep-ph/pastweek')
#             self.assertEqual(
#                 rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')
            
#             flservice.list_articles_by_month = MagicMock(return_value={'not_modified': True,
#                                                                        'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
#             rv = self.client_with_fake_listings.get('/list/hep-ph/1801')
#             self.assertEqual(
#                 rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')

#             flservice.list_articles_by_year = MagicMock(return_value={'not_modified': True,
#                                                                       'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
#             rv = self.client_with_fake_listings.get('/list/hep-ph/18')
#             self.assertEqual(
#                 rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')

#     def test_list_called_from_archive(self):
#         rv = self.client_with_fake_listings.get('/list/?archive=hep-ph&year=08&month=03&submit=Go')        
#         self.assertEqual(rv.status_code, 200)

#         rv = self.client_with_fake_listings.get('/list/?archive=hep-ph&year=08&month=all&submit=Go')        
#         self.assertEqual(rv.status_code, 200)
