import unittest

from bs4 import BeautifulSoup

from tests import path_of_for_test
from tests.test_abs_parser import ABS_FILES
from browse.factory import create_web_app
from browse.services.document.metadata import AbsMetaSession
from browse.domain.license import ASSUMED_LICENSE_URI
from browse.domain.metadata import DocMetadata

import os
import tempfile

from app import app


ABS_FILES =  path_of_for_test('data/abs_files')

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

    def test_all_abs_as_web_pages(self):
        num_files_tested = 0
        for dir_name, subdir_list, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                if os.stat(fname_path).st_size == 0 or not fname_path.endswith('.abs'):
                    continue
                m = AbsMetaSession.parse_abs_file(filename=fname_path)
                rv = self.app.get(f'/abs/{m.arxiv_id}')
                self.assertEqual(rv.status_code, 200)

    def test_canonical_category(self):
        # test these two
        #  ./ftp/adap-org/papers/9303/9303002.abs:Categories: adap-org nlin.AO q-bio.PE
        # ./ftp/adap-org/papers/9303/9303001.abs:Categories: adap-org nlin.AO

        rv = self.app.get('/abs/adap-org/9303002')
        self.assertEqual(rv.status_code, 200)

        html = BeautifulSoup(rv.data.decode('utf-8'),'html.parser')
        subject_elmt = html.find('td','subjects')
        self.assertTrue(subject_elmt,'Should have <td class="subjects"> element')

        sub_txt = subject_elmt.get_text()
        self.assertRegex(sub_txt, r'nlin\.AO', 'should have canonical category of nlin.AO')
        self.assertNotRegex(sub_txt, r'adap-org', 'should NOT have subsumed category name adap-org on subject line')
        self.assertRegex(sub_txt, r'q-bio\.PE', 'should have secondary category of q-bio.PE')
        self.assertNotRegex(sub_txt, r'nlin\.AO.*nlin\.AO', 'should NOT have nlin.AO twice')


