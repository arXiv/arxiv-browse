import unittest

from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup

from tests.test_abs_parser import ABS_FILES
from browse.services.document.metadata import AbsMetaSession
from arxivabs.browse.domain.license import ASSUMED_LICENSE_URI

import os

from app import app


class BrowseLinksTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()

    def test_newer_id(self):
        rv = self.app.get('/abs/1604.08245')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        self.assertIsNotNone(html)

        current_context = html.find('div', 'current')
        self.assertIsNotNone(current_context)
        self.assertEqual(current_context.text, 'cs.MM')

        pn_div = html.find('div', 'prevnext')
        self.assertIsNotNone(pn_div, 'Should have div.prevnext')
        self.assertEqual(pn_div.find_all('span')[0].a['title'],
                         'previous in cs.MM (accesskey p)',
                         'Should have previous span.arrow subtags with correct category')

        self.assertEqual(pn_div.find_all('span')[1].a['title'],
                         'next in cs.MM (accesskey n)',
                         'Should have next span.arrow subtags with correct category')

        switches = html.find_all('div', 'switch')
        self.assertEqual(len(switches),  1,
                         'Should only be one context to switch to')
        self.assertEqual(switches[0].a.text, 'cs',
                         'switch context should be cs')

    def test_older_id(self):
        rv = self.app.get('/abs/ao-sci/9503001')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        self.assertIsNotNone(html)

        current_context = html.find('div', 'current')
        self.assertIsNotNone(current_context)
        self.assertEqual(current_context.text, 'ao-sci')

        pn_div = html.find('div', 'prevnext')
        self.assertIsNotNone(pn_div, 'Should have div.prevnext')

        atags = pn_div.find_all('a')
        self.assertTrue(len(atags) >= 1,
                        'Shold be at least one <a> tags for prev/next')

        self.assertEqual(pn_div.find_all('a')[0]['title'],
                         'previous in ao-sci (accesskey p)',
                         'Should have previous span.arrow subtags with correct category')

        switches = html.find_all('div', 'switch')
        self.assertEqual(len(switches),  0,
                         'Should be no other contxt to switch to')

    def test_older_id_w_canonical(self):
        rv = self.app.get('/abs/physics/9707012')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        self.assertIsNotNone(html)

        current_context = html.find('div', 'current')
        self.assertIsNotNone(current_context)
        self.assertEqual(current_context.text, 'math-ph')

        pn_div = html.find('div', 'prevnext')
        self.assertIsNotNone(pn_div, 'Should have div.prevnext')

        atags = pn_div.find_all('a')
        self.assertTrue(len(atags) >= 1, 'Shold be at least one <a> tags for prev/next')
        
        self.assertEqual(pn_div.find_all('a')[0]['title'],
                         'previous in math-ph (accesskey p)',
                         'Should have previous span.arrow subtags with correct category')

        switches = html.find_all('div', 'switch')
        self.assertEqual(len(switches),  0,
                         'Should be no other contxt to switch to')

        other_atags = html.find('div','list').find_all('a')
        self.assertTrue(other_atags)
        self.assertTrue(len(other_atags) >= 3, "should be at least 3 a tags in list")
        self.assertEqual(other_atags[0]['href'], '/list/math-ph/new')
        self.assertEqual(other_atags[1]['href'], '/list/math-ph/recent')
        self.assertEqual(other_atags[2]['href'], '/list/math-ph/9707')
