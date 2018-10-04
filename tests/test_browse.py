import unittest

from bs4 import BeautifulSoup

from tests.test_abs_parser import ABS_FILES
from browse.services.document.metadata import AbsMetaSession
from browse.domain.license import ASSUMED_LICENSE_URI

import os

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

    def test_all_abs_as_web_pages(self):
        for dir_name, subdir_list, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                if os.stat(fname_path).st_size == 0 or not fname_path.endswith('.abs'):
                    continue
                m = AbsMetaSession.parse_abs_file(filename=fname_path)
                rv = self.app.get(f'/abs/{m.arxiv_id}')
                self.assertEqual(rv.status_code, 200)

    def test_legacy_id_params(self):
        """Test legacy parameters that support specifying arXiv identifer."""
        rv = self.app.get('/abs?id=0704.0600')
        self.assertEqual(rv.status_code, 200, 'id param with new ID')

        rv = self.app.get('/abs?id=adap-org/9303002')
        self.assertEqual(rv.status_code, 200, 'id param with old ID')

        rv = self.app.get('/abs?adap-org/9303002')
        self.assertEqual(rv.status_code, 200, 'singleton case for old IDs')

        rv = self.app.get('/abs?0704.0600')
        self.assertEqual(rv.status_code, 404,
                         'singleton case for new IDs not supported')

        rv = self.app.get('/abs?archive=adap-org&papernum=9303002')
        self.assertEqual(rv.status_code, 200, 'archive and papernum params')

        rv = self.app.get('/abs?archive=foo&papernum=1234567')
        self.assertEqual(rv.status_code, 404)

        rv = self.app.get('/abs/adap-org?papernum=9303002')
        self.assertEqual(rv.status_code, 200,
                         'archive in path with papernum param')

        rv = self.app.get('/abs/adap-org?9303002')
        self.assertEqual(rv.status_code, 200,
                         'archive in path with paper number as singleton')

    def test_fmt_param(self):
        rv = self.app.get('/abs/adap-org/9303001?fmt=txt')
        self.assertEqual(rv.status_code, 200,
                         'get abs with fmt=txt')
        self.assertEqual(rv.mimetype, 'text/plain',
                         'check mimetype is text/plain')

        rv = self.app.get('/abs/adap-org/9303001?fmt=foo')
        # Should this be 400 instead?
        self.assertEqual(rv.status_code, 200,
                         'get abs with fmt=foo')
        self.assertEqual(rv.mimetype, 'text/html',
                         'check mimetype is text/html')

    def test_canonical_category(self):
        # test these two
        #  ./ftp/adap-org/papers/9303/9303002.abs:Categories: adap-org nlin.AO q-bio.PE
        # ./ftp/adap-org/papers/9303/9303001.abs:Categories: adap-org nlin.AO

        rv = self.app.get('/abs/adap-org/9303002')
        self.assertEqual(rv.status_code, 200)

        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        subject_elmt = html.find('td','subjects')
        self.assertTrue(subject_elmt,'Should have <td class="subjects"> element')

        sub_txt = subject_elmt.get_text()
        self.assertRegex(sub_txt, r'nlin\.AO', 'should have canonical category of nlin.AO')
        self.assertNotRegex(sub_txt, r'adap-org', 'should NOT have subsumed category name adap-org on subject line')
        self.assertRegex(sub_txt, r'q-bio\.PE', 'should have secondary category of q-bio.PE')
        self.assertNotRegex(sub_txt, r'nlin\.AO.*nlin\.AO', 'should NOT have nlin.AO twice')

    def test_hep_th_9809096(self):
        # Test for malformed html on this abs
        # https://culibrary.atlassian.net/browse/ARXIVNG-1227
        rv = self.app.get('/abs/hep-th/9809096')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue( "<d<4</h1>" not in rv.data.decode('utf-8'), "Odd malformed HTML in /abs/hep-th/9809096")


    def test_1501_9999(self):
        rv = self.app.get('/abs/1501.99999')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(
            "Luí" in rv.data.decode('utf-8'),
            "Submitter should be properly tex_to_utf for 1501.99999")

        self.assertTrue(
            'href="www.bogus.org"' not in rv.data.decode('utf-8'),
            "hostnames should NOT be turned into links ARXIVNG-1243")

        self.assertTrue(
            'href="bogus.org"' not in rv.data.decode('utf-8'),
            "hostnames should NOT be turned into links ARXIVNG-1243")

        self.assertTrue(
            'href="ftp://ftp.arxiv.org/cheese.txt"' in rv.data.decode('utf-8'),
            "FTP URLs should be turned into links ARXIVNG-1242")
