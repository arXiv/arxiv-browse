"""Test"""

import unittest
from datetime import timedelta

from dateutil import parser

from app import app
from browse.controllers.response_headers import mime_header_date


class ModifiedTest(unittest.TestCase):
    """Test when page is modified and not modified for 200 and 304"""

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app
        self.client = app.test_client()

    def test_modified(self):
        """Test"""
        with self.app.app_context():
            rv = self.client.get('/abs/0704.0600')
            self.assertEqual(rv.status_code, 200)

            last_mod = rv.headers['Last-Modified']
            etag = rv.headers['ETag']

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-Modified-Since': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'if-modified-since': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'IF-MODIFIED-SINCE': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-ModiFIED-SiNCE': last_mod})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-None-Match': etag})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'if-none-match': etag})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'IF-NONE-MATCH': etag})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'iF-NoNE-MaTCH': etag})
            self.assertEqual(rv.status_code, 304)

    def test_not_modified(self):
        """Test when pages is not modified"""
        with self.app.app_context():
            rv = self.client.get('/abs/0704.0600')
            self.assertEqual(rv.status_code, 200)

            mod_dt = parser.parse(rv.headers['Last-Modified'])

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-Modified-Since': mime_header_date(mod_dt)})
            self.assertEqual(rv.status_code, 304)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-Modified-Since': mime_header_date(mod_dt + timedelta(seconds=-1))})
            self.assertEqual(rv.status_code, 200)

            rv = self.client.get('/abs/0704.0600',
                                 headers={'If-None-Match': '"should-never-match"'})
            self.assertEqual(rv.status_code, 200)
