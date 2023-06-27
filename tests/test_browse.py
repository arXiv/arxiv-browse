import os
import unittest
import pytest

from arxiv import taxonomy
from bs4 import BeautifulSoup
from tests.test_fs_abs_parser import ABS_FILES

from browse.domain.license import ASSUMED_LICENSE_URI
from browse.services.documents.fs_implementation.parse_abs import parse_abs_file


@pytest.mark.usefixtures("unittest_add_fake")
class BrowseTest(unittest.TestCase):

    def test_home(self):
        """Test the home page."""
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        for group_key, group_value in taxonomy.definitions.GROUPS.items():
            if group_key == 'grp_test':
                continue
            auths_elmt = html.find('h2', string=group_value['name'])
            self.assertTrue(auths_elmt, f"{group_value['name']} in h2 element")
        self.assertFalse(html.find('h2', string='Test'),
                         "'Test' group should not be shown on homepage")

    def test_tb(self):
        """Test the /tb/<arxiv_id> page."""
        rv = self.client.get('/tb/1901.99999')
        self.assertEqual(rv.status_code, 404)

        rv = self.client.get('/tb/')
        self.assertEqual(rv.status_code, 404)

        rv = self.client.get('/tb/foo')
        self.assertEqual(rv.status_code, 404)

        rv = self.client.get('/tb/0808.4142')
        self.assertEqual(rv.status_code, 200)

        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        h2_elmt = html.find('h2', {'class': 'trackback-heading'})
        h2_txt = h2_elmt.text
        self.assertTrue(h2_elmt, 'Should have <h2> element')
        self.assertEqual(h2_txt, 'Trackbacks for 0808.4142')
        tb_a_tags = html.find_all('a', 'mathjax', rel='external nofollow')
        self.assertGreater(len(tb_a_tags), 1,
                           'There should be more than one <a> tag for trackbacks')
        h1_elmt = html.find('div', id='abs')
        h1_txt = h1_elmt.text
        self.assertTrue(h1_elmt, 'Should have <h1 id="abs"> element')
        self.assertRegex(
            h1_txt,
            r'Observation of the doubly strange b baryon Omega_b-',
            '<h1> element contains title of article')

    def test_tb_recent(self):
        """Test the /tb/recent page."""
        rv = self.client.get('/tb/recent')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.post('/tb/recent', data=dict(views='50'))
        self.assertEqual(rv.status_code, 200, 'POST with integer OK')

        rv = self.client.post('/tb/recent', data=dict(views='bar'))
        self.assertEqual(rv.status_code, 400, 'POST with non-integer not OK')

        rv = self.client.get('/tb/recent/foo')
        self.assertEqual(rv.status_code, 404)

        rv = self.client.post('/tb/recent', data=dict(views='1'))
        self.assertEqual(rv.status_code, 200, 'POST with views==1 OK')
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        tb_a_tags = html.find_all('a', 'mathjax', rel='external nofollow')
        self.assertGreaterEqual(len(tb_a_tags), 1,
                          'There should at least one trackback link')

    def test_stats_today(self):
        """Test the /stats/today page."""
        rv = self.client.get('/stats/today')
        self.assertEqual(rv.status_code, 200)
        rv = self.client.get('/stats/today?date=20190102')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        csv_dl_elmt = html.find(
            'a', {'href': '/stats/get_hourly?date=20190102'})
        self.assertIsNotNone(csv_dl_elmt,
                             'csv download link exists')

    def test_stats_monthly_downloads(self):
        """Test the /stats/monthly_downloads page."""
        rv = self.client.get('/stats/monthly_downloads')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        csv_dl_elmt = html.find('a', {'href': '/stats/get_monthly_downloads'})
        self.assertIsNotNone(csv_dl_elmt,
                             'csv download link exists')

    def test_stats_monthly_submissions(self):
        """Test the /stats/monthly_submissions page."""
        rv = self.client.get('/stats/monthly_submissions')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        csv_dl_elmt = html.find(
            'a', {'href': '/stats/get_monthly_submissions'})
        self.assertIsNotNone(csv_dl_elmt,
                             'csv download link exists')

    def test_abs_without_license_field(self):
        f1 = ABS_FILES + '/ftp/arxiv/papers/0704/0704.0001.abs'
        m = parse_abs_file(filename=f1)

        rv = self.client.get('/abs/0704.0001')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(m.license.recorded_uri, None,
                         '0704.0001 should have no license in abs')
        self.assertEqual(m.license.effective_uri, ASSUMED_LICENSE_URI,
                         '0704.0001 should get assumed license')
        assert b'http://arxiv.org/licenses/assumed-1991-2003/' in rv.data, \
            'abs/0704.0001 should be displayed with assumed-1991-2003 license'

    def test_abs_with_license_field(self):
        f1 = ABS_FILES + '/ftp/arxiv/papers/0704/0704.0600.abs'
        m = parse_abs_file(filename=f1)

        self.assertNotEqual(m.license, None)
        self.assertNotEqual(m.license.recorded_uri, None)
        self.assertEqual(m.license.recorded_uri,
                         m.license.effective_uri)
        self.assertNotEqual(
            m.license.recorded_uri,
            'http://arxiv.org/licenses/assumed-1991-2003/')

        rv = self.client.get('/abs/0704.0600')
        self.assertEqual(rv.status_code, 200)

        self.assertRegex(
            rv.data.decode('utf-8'), m.license.effective_uri,
            'should be displayed with its license')

    def test_missing_paper(self):
        rv = self.client.get('/abs/1805.0001')
        self.assertEqual(rv.status_code, 301)

    def test_abs_with_truncated_author_list(self):
        rv = self.client.get('/abs/1411.4413')
        assert b'additional authors not shown' in rv.data, \
            'abs/1411.4413 should have a truncate author list'

    def test_all_abs_as_web_pages(self):
        for dir_name, subdir_list, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                if os.stat(fname_path).st_size == 0 or not fname_path.endswith('.abs'):
                    continue
                m = parse_abs_file(filename=fname_path)
                rv = self.client.get(f'/abs/{m.arxiv_id}')
                self.assertEqual(rv.status_code, 200)

    def test_legacy_id_params(self):
        """Test legacy parameters that support specifying arXiv identifer."""
        rv = self.client.get('/abs?id=0704.0600')
        self.assertEqual(rv.status_code, 200, 'id param with new ID')

        rv = self.client.get('/abs?id=adap-org/9303002')
        self.assertEqual(rv.status_code, 200, 'id param with old ID')

        rv = self.client.get('/abs?adap-org/9303002')
        self.assertEqual(rv.status_code, 200, 'singleton case for old IDs')

        rv = self.client.get('/abs?archive=adap-org&papernum=9303002')
        self.assertEqual(rv.status_code, 200, 'archive and papernum params')

        rv = self.client.get('/abs/adap-org?papernum=9303002')
        self.assertEqual(rv.status_code, 200,
                         'archive in path with papernum param')

        rv = self.client.get('/abs/adap-org?9303002')
        self.assertEqual(rv.status_code, 200,
                         'archive in path with paper number as singleton')

    def test_fmt_param(self):
        """Test fmt request parameter."""
        rv = self.client.get('/abs/adap-org/9303001?fmt=txt')
        self.assertEqual(rv.status_code, 200,
                         'get abs with fmt=txt')
        self.assertEqual(rv.mimetype, 'text/plain',
                         'check mimetype is text/plain')

        rv = self.client.get('/abs/adap-org/9303001?fmt=foo')
        # Should this be 400 instead?
        self.assertEqual(rv.status_code, 200,
                         'get abs with fmt=foo')
        self.assertEqual(rv.mimetype, 'text/html',
                         'check mimetype is text/html')

    def test_subsumed_archives(self):
        """Test correct category display of subsumed archives."""
        rv = self.client.get('/abs/adap-org/9303002')
        self.assertEqual(rv.status_code, 200)

        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        subject_elmt = html.find('td', 'subjects')
        self.assertTrue(
            subject_elmt, 'Should have <td class="subjects"> element')

        sub_txt = subject_elmt.text
        self.assertRegex(sub_txt, r'nlin\.AO',
                         'should have canonical category of nlin.AO')
        self.assertNotRegex(
            sub_txt,
            r'adap-org',
            'should NOT have subsumed archive adap-org on subject line')
        self.assertRegex(sub_txt, r'q-bio\.PE',
                         'should have secondary category of q-bio.PE')
        self.assertNotRegex(sub_txt, r'nlin\.AO.*nlin\.AO',
                            'should NOT have nlin.AO twice')

    def test_requested_version(self):
        """Test that requested version is reflected in display fields."""
        # We expect the requested version to appear in the breadcrum header,
        # header title and download links
        rv = self.client.get('/abs/physics/9707012')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        div_elmt = html.find('div', class_= 'header-breadcrumbs')
        div_txt = div_elmt.text
        self.assertRegex(div_txt, r'arXiv:physics\/9707012')
        self.assertNotRegex(div_txt, r'arXiv:physics\/9707012v')

        title_elmt = html.find('title')
        title_txt = title_elmt.text
        self.assertRegex(title_txt, r'physics\/9707012')
        self.assertNotRegex(title_txt, r'arXiv:physics\/9707012v')
        pdf_dl_elmt = html.find('a', {'href': '/pdf/physics/9707012.pdf'})
        self.assertIsNotNone(pdf_dl_elmt,
                             'pdf download link without version affix exists')
        pdf_dl_elmt = html.find('a', {'href': '/pdf/physics/9707012v'})
        self.assertIsNone(
            pdf_dl_elmt, 'pdf download link with version affix does not exist')

        rv = self.client.get('/abs/physics/9707012v4')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        div_elmt = html.find('div', class_='header-breadcrumbs')
        div_txt = div_elmt.text
        self.assertRegex(div_txt, r'arXiv:physics\/9707012v4')

        title_elmt = html.find('title')
        title_txt = title_elmt.text
        self.assertRegex(title_txt, r'physics\/9707012v4')

        pdf_dl_elmt = html.find('a', {'href': '/pdf/physics/9707012v4.pdf'})
        self.assertIsNotNone(pdf_dl_elmt,
                             'pdf download link with version affix exists')
        pdf_dl_elmt = html.find('a', {'href': '/pdf/physics/9707012.pdf'})
        self.assertIsNone(pdf_dl_elmt,
                          'pdf download link without version affix does not exist')

    def test_hep_th_9809096(self):
        """Test for malformed html fix in hep-th/9809096 (ARXIVNG-1227)."""
        rv = self.client.get('/abs/hep-th/9809096')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue("<d<4</h1>" not in rv.data.decode('utf-8'),
                        "Odd malformed HTML in /abs/hep-th/9809096")

    def test_1501_9999(self):
        """Test encoding and linking issues in 1501.99999."""
        rv = self.client.get('/abs/1501.99999')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(
            "Luí" in rv.data.decode('utf-8'),
            "Submitter should be properly tex_to_utf for 1501.99999")

        self.assertTrue(
            'π_1^{{é}t}' in rv.data.decode('utf-8'),
            "abstract field should include π, é characters for 1501.99999"
        )

        self.assertTrue(
            'href="www.bogus.org"' not in rv.data.decode('utf-8'),
            "hostnames should NOT be turned into links ARXIVNG-1243")

        self.assertTrue(
            'href="bogus.org"' not in rv.data.decode('utf-8'),
            "hostnames should NOT be turned into links ARXIVNG-1243")

        self.assertTrue(
            'href="ftp://ftp.arxiv.org/cheese.txt"' in rv.data.decode('utf-8'),
            "FTP URLs should be turned into links ARXIVNG-1242")

        self.assertTrue(
            'MPES &amp;amp; Oxford' not in rv.data.decode('utf-8'),
            "Ampersand in author affiliation should not be double escaped")

    def test_160408245(self):
        """Test linking in 1604.08245."""
        id = '1604.08245'
        rv = self.client.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200, f'status 200 for {id}')

        badtag =\
            '<a 0316.2013"="" abs="" href="http://'

        self.assertTrue(
            badtag not in rv.data.decode('utf-8'),
            f"should not have malformed <a> tag in {id}")

        badtag2 = 'href="http://learnrnd.com/news.php?id=Magnetic_3D_Bio_Printing]"'
        self.assertTrue(
            badtag2 not in rv.data.decode('utf-8'),
            "link should not include closing square bracket")

    @unittest.skip("TODO ARXIVNG-1246, may require refactoring jinja filters")
    def test_arxivng_1246(self):
        """Test urlize fix for comments in 1604.08245v1 (ARXIVNG-1246)."""
        id = '1604.08245'
        rv = self.client.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200)

        goodtag = '<a href="http://www.tandfonline.com/doi/abs/10.1080/15980316.2013.860928?journalCode=tjid20">'
        self.assertTrue(goodtag in rv.data.decode('utf-8'),
                        'should have good tag, arxiv-id-to-url and urlize'
                        ' should not stomp on each others work, might need'
                        ' to combine them.')

    def test_authors_and_arxivId_in_title(self):
        id = '1501.99999'
        rv = self.client.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        title_elmt = html.find('h1', 'title')
        self.assertTrue(title_elmt, 'Should title element')

        ida = title_elmt.find('a')
        self.assertTrue(ida, 'Should be <a> tag in title')

        self.assertIsNotNone(ida['href'], '<a> tag in title should have href')
        self.assertEqual(ida['href'], 'https://arxiv.org/abs/1501.99998')

        self.assertEqual(ida.text, '1501.99998')

        au_a_tags = html.find('div', 'authors').find_all('a')
        self.assertGreater(len(au_a_tags), 1,
                           'Should be some a tags for authors')
        self.assertNotIn('query=The', au_a_tags[0]['href'],
                         'Collaboration author query should not have "The"')
        self.assertEqual(au_a_tags[0].text, 'SuperSuper Collaboration')

    def test_long_author_colab(self):
        id = '1501.05201'
        rv = self.client.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        auths_elmt = html.find('div', 'authors')
        self.assertTrue(auths_elmt, 'Should authors div element')

        a_tags = auths_elmt.find_all('a')
        self.assertEqual(
            len(a_tags), 2, 'Should be two <a> tags in authors div')

        colab = a_tags[1]

        self.assertIsNotNone(
            colab['href'], '<a> tag in title should have href')
        self.assertEqual(
            colab['href'], 'https://arxiv.org/search/physics?searchtype=author&query=ILL%2FESS%2FLiU+collaboration')
        self.assertEqual(
            colab.text, 'ILL/ESS/LiU collaboration for the development of the B10 detector technology in the framework of the CRISP project')

    @unittest.skip("In current implementation, conflicts with comma test below.")
    def test_space_in_author_list(self):
        id = '1210.8438'
        rv = self.client.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')

        auths_elmt = html.find('div', 'authors')
        self.assertTrue(auths_elmt, 'Should authors div element')

        self.assertIn('Zhe (Rita) Liang,', auths_elmt.text,
                      'Should be a space after (Rita)')

    def test_comma_in_author_list(self):
        id = '0704.0155'
        rv = self.client.get('/abs/' + id)
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        auths_elmt = html.find('div', 'authors')
        self.assertTrue(auths_elmt, 'Should authors div element')
        self.assertNotIn(' ,', auths_elmt.text,
                         'Should not add extra spaces before commas')

    def test_psi_in_abs(self):
        # see https://arxiv-org.atlassian.net/browse/ARXIVNG-1612
        # "phi being displayed as varphi in abstract on /abs page"
        # phi being displayed incorrectly in abstract on /abs page
        rv = self.client.get('/abs/1901.05426')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        abs_elmt = html.find('blockquote', 'abstract')
        self.assertTrue(abs_elmt, 'Should have abstract div element')
        self.assertNotIn('$ φ$', abs_elmt.text,
                         'TeX psi in abstract should not get converted to UTF8')
        self.assertNotIn('$j(φ,L)$', abs_elmt.text,
                         'TeX psi in abstract should not get converted to UTF8')
        self.assertIn('The phase difference $\\phi$, between the superconducting',
                      abs_elmt.text,
                      "Expecting uncoverted $\\phi$ in html abstract.")

    def test_year(self):
        rv = self.client.get('/year/astro-ph/09')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.get('/year/astro-ph/')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.get('/year/astro-ph')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.get('/year/astro-ph/09/')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.get('/year')
        self.assertEqual(rv.status_code, 404)

        rv = self.client.get('/year/astro-ph/9999')
        self.assertEqual(rv.status_code, 307,
                         'Future year should cause temporary redirect')

        rv = self.client.get('/year/fakearchive/01')
        self.assertNotEqual(rv.status_code, 200)
        self.assertLess(rv.status_code, 500, 'should not cause a 5XX')

        rv = self.client.get('/year/002/0000')
        self.assertLess(rv.status_code, 500, 'should not cause a 5XX')

        rv = self.client.get('/year/astro-py/9223372036854775808')
        self.assertLess(rv.status_code, 500, 'should not cause a 5XX')

    def test_secondary_order(self):
        rv = self.client.get('/abs/0906.3421')
        self.assertIn(
            'Statistical Mechanics (cond-mat.stat-mech); Mathematical Physics (math-ph)',
            rv.data.decode('utf-8'),
            'Secondary categories should be orderd by category id ARXIVNG-2066')

    def test_covid_message(self):
        rv = self.client.get('/abs/physics/9707012')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        self.assertIsNone(html.find('div', class_='message-special'))
        covid_papers = ['2004.05256', '2004.08990', '2004.09471']
        for id in covid_papers:
            rv = self.client.get(f'/abs/{id}')
            self.assertEqual(rv.status_code, 200)
            html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
            self.assertIsNotNone(html.find('div', class_='message-special'))

    def test_tex2utf_in_jref(self):
        rv = self.client.get('/abs/2006.02835')
        self.assertEqual(rv.status_code, 200)
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        jref_elmt = html.find('td', 'jref')
        self.assertTrue(jref_elmt, 'Should have jref td element')
        self.assertIn('RIMS Kôkyûroku Bessatsu', jref_elmt.text, 'Expecting converted TeX in journal reference field')


    def test_bibtex(self):
        for dir_name, _, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                if os.stat(fname_path).st_size == 0 or not fname_path.endswith('.abs'):
                    continue
                dm = parse_abs_file(filename=fname_path)
                rv = self.client.get(f'/bibtex/{dm.arxiv_id}')
                self.assertEqual(rv.status_code, 200, f'checking /bibtex for {dm.arxiv_id}')

    def test_2004_02153(self):
        """Test when more than one \\ begins a line in the .abs file. ARXIVNG-3128"""
        rv = self.client.get('/abs/2004.02153')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("We construct global generalized solutions to the chemotaxis system",
                      txt,
                      "Expect the abstract including the first sentence.")
        self.assertIn("\\\\ v_t = \\Delta", txt, "Expect the TeX case")
        self.assertIn("collapse into a persistent Dirac distribution.",
                      txt,
                      "Expect the abstract including the last sentence.")

    def test_no_prev(self):
        rv = self.client.get('/abs/math-ph/0509001')
        html = BeautifulSoup(rv.data.decode('utf-8'), 'html.parser')
        link = html.find('a', class_='next-url')
        assert link
        assert link['href'] == '/abs/math-ph/0509002'

        link = html.find('a', class_='prev-url')
        assert link is None

    def test_withdrawn_msg(self):
        """Test that a withdrawn abs gets a withdrawn warning"""
        rv = self.client.get('/abs/0704.0615')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("This paper has been withdrawn", txt, "Expect a withdrawn message.")

        rv = self.client.get('/abs/0704.0615v1')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn", txt, "Expect a withdrawn message.")


    def test_withdrawn_by_admin(self):
        """Test that a withdrawn abs gets a withdrawn warning from admin"""
        rv = self.client.get('/abs/2101.10016')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("This paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message.")

        self.assertNotIn('href="/e-print/2101.10016"', txt,
                         "Should not have link to source since it is useless, src is empty")

        rv = self.client.get('/abs/2101.10016v8')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("This paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message.")


        rv = self.client.get('/abs/2101.10016v7')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")

        rv = self.client.get('/abs/2101.10016v6')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")

        rv = self.client.get('/abs/2101.10016v5')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")

        rv = self.client.get('/abs/2101.10016v4')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")

        rv = self.client.get('/abs/2101.10016v3')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")

        rv = self.client.get('/abs/2101.10016v2')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")

        rv = self.client.get('/abs/2101.10016v1')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("A newer version of this paper has been withdrawn by arXiv Admin", txt,
                      "Expect an admin withdrawn message on earlier verison.")
        self.assertIn('href="/pdf/2101.10016', txt,
                         "Should have link to pdf")


    def test_withdrawn_then_new_version(self):
        """Test where v2 is withdrawn but then there is a non-withdrawn v3."""
        rv = self.client.get('/abs/astro-ph/9709175')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertNotIn("This paper has been withdrawn", txt,
                      "Do not expect a withdrawn message in latest version.")

        rv = self.client.get('/abs/astro-ph/9709175v3')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertNotIn("This paper has been withdrawn", txt,
                      "Do not expect a withdrawn message in v3.")


        rv = self.client.get('/abs/astro-ph/9709175v2')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("This paper has been withdrawn", txt,
                      "Expect a withdrawn message in v2.")


        rv = self.client.get('/abs/astro-ph/9709175v1')
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')
        self.assertIn("paper has been withdrawn", txt,
                      "Expect a withdrawn message in v1 since v2 is withdrawn.")

        self.assertIn("Older arxiv papers may lack submitter name", txt,
                      "Expect a message about lack of submitter name on old paper")
