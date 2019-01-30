import unittest
import re
from hamcrest import *
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from tests.test_abs_parser import ABS_FILES
from browse.services.document.metadata import AbsMetaSession
from browse.domain.license import ASSUMED_LICENSE_URI
from browse.services.listing.fake_listings import FakeListingFilesService
from browse.services.listing import ListingService
import os

from app import app


class ListPageTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''

        # BDC34 there should be a better way of setting up a
        # service in the app. or maybe not?
        app.config['listing_service'] = FakeListingFilesService()
        # NB all /list requests return the same data with FakeListingFilesService
        # that is the month and category do not affect the returned list.

        self.app = app.test_client()

    def test_basic_lists(self):
        rv = self.app.get('/list/hep-ph/0901')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/hep-ph/09')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/hep-ph/new')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/hep-ph/current')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/hep-ph/pastweek')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/hep-ph/recent')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/hep-ph/0901?skip=925&show=25')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/astro-ph/04')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/math/92')
        self.assertEqual(rv.status_code, 200)
        self.assertNotEqual(rv.headers.get('Expires', None), None)

        rv = self.app.get('/list/math/9201')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0101')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0102')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0103')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0104')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0105')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0106')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0107')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0108')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0109')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0110')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0111')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0112')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/01')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/18')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/20')  # year 2020
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/30')  # year 2030
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/200101')
        self.assertEqual(rv.status_code, 200)

    def test_listing_authors(self):
        rv = self.app.get('/list/hep-ph/0901')
        self.assertEqual(rv.status_code, 200)
        au = b'Eqab M. Rabei'
        assert au in rv.data, f'Simple check for author {au} in response.'

        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        auDivs = html.find_all('div', 'list-authors')
        assert_that(auDivs, not_none())
        assert_that(len(auDivs), greater_than(
            5), 'Should have some .list-author divs')

        first_aus = auDivs[0].find_all('a')
        assert_that(first_aus, has_length(4),
                    'expect 4 <a> tags for first artcile "Fractional WKB Approximation"')

        assert_that(first_aus[0].get_text(), equal_to('Eqab M. Rabei'))
        assert_that(first_aus[1].get_text(),
                    equal_to('Ibrahim M. A. Altarazi'))
        assert_that(first_aus[2].get_text(), equal_to('Sami I. Muslih'))
        assert_that(first_aus[3].get_text(), equal_to('Dumitru Baleanu'))

        assert_that(auDivs[0].get_text(), is_not(contains_string(' ,')),
                    'Should not have a comma with a space in front of it')

    def test_paging_first(self):
        rv = self.app.get('/list/hep-ph/0901')
        self.assertEqual(rv.status_code, 200)

        rvdata = rv.data.decode('utf-8')
        html = BeautifulSoup(rvdata, 'html.parser')

        paging = html.find(id='dlpage').find_all('div')[0]
        assert_that(paging, not_none())
        tgs = paging.find_all(['span', 'a'])
        assert_that(tgs, not_none())
        assert_that(len(tgs), 6)

        assert_that(tgs[0].name, equal_to('span'))
        assert_that(tgs[0].get_text(), equal_to('1-25'))

        assert_that(tgs[1].name, equal_to('a'))
        assert_that(tgs[1].get_text(), equal_to('26-50'))

        assert_that(tgs[2].name, equal_to('a'))
        assert_that(tgs[2].get_text(), equal_to('51-75'))

        assert_that(tgs[3].name, equal_to('a'))
        assert_that(tgs[3].get_text(), equal_to('76-100'))

        assert_that(tgs[4].name, equal_to('span'))
        assert_that(tgs[4].get_text(), equal_to('...'))

        assert_that(tgs[5].name, equal_to('a'))
        assert_that(tgs[5].get_text(), equal_to('1001-1001'))

        # find the first article index tag
        first_index_atag = html.find(id='articles').find_all(
            'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
        assert_that(first_index_atag, not_none())
        assert_that(first_index_atag['name'], equal_to('item1'))
        assert_that(first_index_atag.string, equal_to('[1]'))

    def test_paging_second(self):
        rv = self.app.get('/list/hep-ph/0901?skip=25&show=25')
        self.assertEqual(rv.status_code, 200)

        rvdata = rv.data.decode('utf-8')
        html = BeautifulSoup(rvdata, 'html.parser')

        paging = html.find(id='dlpage').find_all('div')[0]
        assert_that(paging, not_none())
        tgs = paging.find_all(['span', 'a'])
        assert_that(tgs, not_none())
        assert_that(len(tgs), 7)

        assert_that(tgs[0].name, equal_to('a'))
        assert_that(tgs[0].get_text(), equal_to('1-25'))

        assert_that(tgs[1].name, equal_to('span'))
        assert_that(tgs[1].get_text(), equal_to('26-50'))

        assert_that(tgs[2].name, equal_to('a'))
        assert_that(tgs[2].get_text(), equal_to('51-75'))

        assert_that(tgs[3].name, equal_to('a'))
        assert_that(tgs[3].get_text(), equal_to('76-100'))

        assert_that(tgs[4].name, equal_to('a'))
        assert_that(tgs[4].get_text(), equal_to('101-125'))

        assert_that(tgs[5].name, equal_to('span'))
        assert_that(tgs[5].get_text(), equal_to('...'))

        assert_that(tgs[6].name, equal_to('a'))
        assert_that(tgs[6].get_text(), equal_to('1001-1001'))

        # find the first article index tag
        first_index_atag = html.find(id='articles').find_all(
            'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
        assert_that(first_index_atag, not_none())
        assert_that(first_index_atag['name'], is_not(
            'item1'), 'first item index should not be 1')
        assert_that(first_index_atag.string, equal_to('[26]'))

    def test_paging_middle(self):
        rv = self.app.get('/list/hep-ph/0901?skip=175&show=25')
        self.assertEqual(rv.status_code, 200)

        rvdata = rv.data.decode('utf-8')
        html = BeautifulSoup(rvdata, 'html.parser')

        paging = html.find(id='dlpage').find_all('div')[0]
        assert_that(paging, not_none())
        tgs = paging.find_all(['span', 'a'])
        assert_that(tgs, not_none())
        assert_that(len(tgs), 7)

        assert_that(tgs[0].name, equal_to('a'))
        assert_that(tgs[0].get_text(), equal_to('1-25'))

        assert_that(tgs[1].name, equal_to('span'))
        assert_that(tgs[1].get_text(), equal_to('...'))

        assert_that(tgs[2].name, equal_to('a'))
        assert_that(tgs[2].get_text(), equal_to('101-125'))

        assert_that(tgs[3].name, equal_to('a'))
        assert_that(tgs[3].get_text(), equal_to('126-150'))

        assert_that(tgs[4].name, equal_to('a'))
        assert_that(tgs[4].get_text(), equal_to('151-175'))

        assert_that(tgs[5].name, equal_to('span'))
        assert_that(tgs[5].get_text(), equal_to('176-200'))

        assert_that(tgs[6].name, equal_to('a'))
        assert_that(tgs[6].get_text(), equal_to('201-225'))

        assert_that(tgs[7].name, equal_to('a'))
        assert_that(tgs[7].get_text(), equal_to('226-250'))

        assert_that(tgs[8].name, equal_to('a'))
        assert_that(tgs[8].get_text(), equal_to('251-275'))

        assert_that(tgs[9].name, equal_to('span'))
        assert_that(tgs[9].get_text(), equal_to('...'))

        assert_that(tgs[10].name, equal_to('a'))
        assert_that(tgs[10].get_text(), equal_to('1001-1001'))

        # find the first article index tag
        first_index_atag = html.find(id='articles').find_all(
            'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
        assert_that(first_index_atag, not_none())
        assert_that(first_index_atag['name'], is_not(
            'item1'), 'first item index should not be 1')
        assert_that(first_index_atag.string, equal_to('[176]'))

    def test_paging_last(self):
        rv = self.app.get('/list/hep-ph/0901?skip=1000&show=25')
        self.assertEqual(rv.status_code, 200)

        rvdata = rv.data.decode('utf-8')
        html = BeautifulSoup(rvdata, 'html.parser')

        paging = html.find(id='dlpage').find_all('div')[0]
        assert_that(paging, not_none())
        tgs = paging.find_all(['span', 'a'])
        assert_that(tgs, not_none())
        assert_that(len(tgs), 7)

        assert_that(tgs[0].name, equal_to('a'))
        assert_that(tgs[0].get_text(), equal_to('1-25'))

        assert_that(tgs[1].name, equal_to('span'))
        assert_that(tgs[1].get_text(), equal_to('...'))

        assert_that(tgs[2].name, equal_to('a'))
        assert_that(tgs[2].get_text(), equal_to('926-950'))

        assert_that(tgs[3].name, equal_to('a'))
        assert_that(tgs[3].get_text(), equal_to('951-975'))

        assert_that(tgs[4].name, equal_to('a'))
        assert_that(tgs[4].get_text(), equal_to('976-1000'))

        assert_that(tgs[5].name, equal_to('span'))
        assert_that(tgs[5].get_text(), equal_to('1001-1001'))

        # find the first article index tag
        first_index_atag = html.find(id='articles').find_all(
            'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
        assert_that(first_index_atag, not_none())
        assert_that(first_index_atag['name'], is_not(
            'item1'), 'first item index should not be 1')
        assert_that(first_index_atag.string, equal_to('[1001]'))

    def test_paging_penultimate(self):
        rv = self.app.get('/list/hep-ph/0901?skip=975&show=25')
        self.assertEqual(rv.status_code, 200)

        rvdata = rv.data.decode('utf-8')
        html = BeautifulSoup(rvdata, 'html.parser')

        paging = html.find(id='dlpage').find_all('div')[0]
        assert_that(paging, not_none())
        tgs = paging.find_all(['span', 'a'])
        assert_that(tgs, not_none())
        assert_that(len(tgs), 7)

        assert_that(tgs[0].name, equal_to('a'))
        assert_that(tgs[0].get_text(), equal_to('1-25'))

        assert_that(tgs[1].name, equal_to('span'))
        assert_that(tgs[1].get_text(), equal_to('...'))

        assert_that(tgs[2].name, equal_to('a'))
        assert_that(tgs[2].get_text(), equal_to('901-925'))

        assert_that(tgs[3].name, equal_to('a'))
        assert_that(tgs[3].get_text(), equal_to('926-950'))

        assert_that(tgs[4].name, equal_to('a'))
        assert_that(tgs[4].get_text(), equal_to('951-975'))

        assert_that(tgs[5].name, equal_to('span'))
        assert_that(tgs[5].get_text(), equal_to('976-1000'))

        assert_that(tgs[6].name, equal_to('a'))
        assert_that(tgs[6].get_text(), equal_to('1001-1001'))

        # find the first article index tag
        first_index_atag = html.find(id='articles').find_all(
            'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
        assert_that(first_index_atag, not_none())
        assert_that(first_index_atag['name'], is_not(
            'item1'), 'first item index should not be 1')
        assert_that(first_index_atag.string, equal_to('[976]'))

    def test_paging_925(self):
        rv = self.app.get('/list/hep-ph/0901?skip=925&show=25')
        self.assertEqual(rv.status_code, 200)

        rvdata = rv.data.decode('utf-8')
        html = BeautifulSoup(rvdata, 'html.parser')

        paging = html.find(id='dlpage').find_all('div')[0]
        assert_that(paging, not_none())
        tgs = paging.find_all(['span', 'a'])
        assert_that(tgs, not_none())
        assert_that(len(tgs), 7)

        assert_that(tgs[0].name, equal_to('a'))
        assert_that(tgs[0].get_text(), equal_to('1-25'))

        assert_that(tgs[1].name, equal_to('span'))
        assert_that(tgs[1].get_text(), equal_to('...'))

        assert_that(tgs[2].name, equal_to('a'))
        assert_that(tgs[2].get_text(), equal_to('851-875'))

        assert_that(tgs[3].name, equal_to('a'))
        assert_that(tgs[3].get_text(), equal_to('876-900'))

        assert_that(tgs[4].name, equal_to('a'))
        assert_that(tgs[4].get_text(), equal_to('901-925'))

        assert_that(tgs[5].name, equal_to('span'))
        assert_that(tgs[5].get_text(), equal_to('926-950'))

        assert_that(tgs[6].name, equal_to('a'))
        assert_that(tgs[6].get_text(), equal_to('951-975'))

        assert_that(tgs[7].name, equal_to('a'))
        assert_that(tgs[7].get_text(), equal_to('976-1000'))

        assert_that(tgs[8].name, equal_to('a'))
        assert_that(tgs[8].get_text(), equal_to('1001-1001'))

        # find the first article index tag
        first_index_atag = html.find(id='articles').find_all(
            'dt')[0].find('a', string=re.compile(r'\[\d*\]'))
        assert_that(first_index_atag, not_none())
        assert_that(first_index_atag['name'], is_not(
            'item1'), 'first item index should not be 1')
        assert_that(first_index_atag.string, equal_to('[926]'))

    def test_odd_requests(self):
        rv = self.app.get('/list/hep-ph/0901?skip=925&show=1000000')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/list/hep-ph/bogusTimePeriod')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/junkarchive')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/ao-si/0901?skip=925&show=25')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0100')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0113')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/0199')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/200199')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/2')
        self.assertNotEqual(rv.status_code, 200)

        rv = self.app.get('/list/math/2001999999')
        self.assertNotEqual(rv.status_code, 200)

    def test_abs_service(self):
        service = ListingService()
        assert_that(calling(service.list_articles_by_year).with_args('a', 1, 1, 1, 1),
                    raises(NotImplementedError))
        assert_that(calling(service.list_articles_by_month).with_args('a', 1, 1, 1, 1),
                    raises(NotImplementedError))
        assert_that(calling(service.list_new_articles).with_args('a', 1, 1),
                    raises(NotImplementedError))
        assert_that(calling(service.list_pastweek_articles).with_args('a', 1, 1),
                    raises(NotImplementedError))

        assert_that(service.version(), is_not(None))

    def test_not_modified_from_listing_service(self):
        flservice = app.config['listing_service']
        flservice.list_new_articles = MagicMock(return_value={'not_modified': True,
                                                              'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
        rv = self.app.get('/list/hep-ph/new')
        self.assertEqual(
            rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')

        flservice.list_pastweek_articles = MagicMock(return_value={'not_modified': True,
                                                                   'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
        rv = self.app.get('/list/hep-ph/recent')
        self.assertEqual(
            rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')        
        rv = self.app.get('/list/hep-ph/pastweek')
        self.assertEqual(
            rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')
        
        flservice.list_articles_by_month = MagicMock(return_value={'not_modified': True,
                                                                    'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
        rv = self.app.get('/list/hep-ph/1801')
        self.assertEqual(
            rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')

        flservice.list_articles_by_year = MagicMock(return_value={'not_modified': True,
                                                                  'expires': 'Wed, 21 Oct 2015 07:28:00 GMT'})
        rv = self.app.get('/list/hep-ph/18')
        self.assertEqual(
            rv.status_code, 304, '/list controller should return 304 when service indicates not-modified')
