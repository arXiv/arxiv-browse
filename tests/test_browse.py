import unittest

from tests.test_abs_parser import ABS_FILES
from browse.factory import create_web_app
from browse.services.document.metadata import AbsMetaSession
from browse.domain.license import ASSUMED_LICENSE_URI

import os
import tempfile

from app import app


class BrowseTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        app.config['APPLICATION_ROOT'] = ''
        self.app = app.test_client()

    def test_abs_without_license_field(self):
        f1 = ABS_FILES + '/ftp/arxiv/papers/0704/0704.0001.abs'
        m = AbsMetaSession.parse_abs_file(filename=f1)

        rv = self.app.get('/abs/0704.0001')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(m.license.recorded_uri, None,
                         '0704.0001 should have no license in abs')
        self.assertEqual(m.license.effective_uri, ASSUMED_LICENSE_URI,
                         '0704.0001 should get assumed license')
        assert b'http://arxiv.org/licenses/assumed-1991-2003/' in rv.data, \
            'abs/0704.0001 should be displayed with assumed-1991-2003 license'

    def test_abs_with_license_field(self):
        f1 = ABS_FILES + '/ftp/arxiv/papers/0704/0704.0600.abs'
        m = AbsMetaSession.parse_abs_file(filename=f1)

        self.assertNotEqual(m.license, None)
        self.assertNotEqual(m.license.recorded_uri, None)
        self.assertEqual(m.license.recorded_uri,
                         m.license.effective_uri)
        self.assertNotEqual(
            m.license.recorded_uri,
            'http://arxiv.org/licenses/assumed-1991-2003/')

        rv = self.app.get('/abs/0704.0600')
        self.assertEqual(rv.status_code, 200)

        self.assertRegex(
            rv.data.decode('utf-8'), m.license.effective_uri,
            'should be displayed with its license')

    def test_missing_paper(self):
        rv = self.app.get('/abs/1805.0001')
        self.assertEqual(rv.status_code, 301)

    def test_abs_with_truncated_author_list(self):
        rv = self.app.get('/abs/1411.4413')
        assert b'additional authors not shown' in rv.data, \
            'abs/1411.4413 should have a truncate author list'


if __name__ == '__main__':
    unittest.main()
