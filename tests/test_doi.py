import unittest

from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup

from tests.test_abs_parser import ABS_FILES
from browse.services.document.metadata import AbsMetaSession
from browse.domain.license import ASSUMED_LICENSE_URI

import os

from app import app


class DoiTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()

    def test_doi_9503001(self):
        # test for ARXIVNG-1201, messed up doi text and href
        rv = self.app.get('/abs/ao-sci/9503001')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        self.assertIsNotNone(html)

        doi_a = html.find('td', 'msc_classes').find('a')
        self.assertIsNotNone(doi_a)
        self.assertEqual(doi_a.text,
                         '10.1175/1520-0469(1996)053<0946:ASTFHH>2.0.CO;2',
                         'DOI links should deal with strange characters with no problems')

        self.assertIsNotNone(doi_a['href'])
        parsed_url = urlparse(doi_a['href'])
        self.assertIsNotNone(parsed_url)

        self.assertEqual(parsed_url.path, '/ct', 'href should be to arXiv /ct')
        qs = parse_qs(parsed_url.query)
        self.assertIsNotNone(qs)

        self.assertTrue('v' in qs, 'query to /ct must have v parameter')
        self.assertTrue('url' in qs, 'query to /ct must have parameter url')

        doiurl = urlparse(unquote(qs['url'][0]))
        self.assertIsNotNone(doiurl,
                             'url query part should deurlencode to a URL')

        self.assertEqual(doiurl.netloc, 'dx.doi.org',
                         'decoded URL from CT should have DOI resolver hostname')
        self.assertEqual(doiurl.path, '/10.1175/1520-0469(1996)053<0946:ASTFHH>2.0.CO',
                         'path of doi.org URL should be to expected DOI')
