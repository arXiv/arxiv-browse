from hamcrest import *
import unittest
from functools import partial

from app import app
from browse.filters import doi_urls, arxiv_id_urls


class Jinja_Custom_Fitlers_Test(unittest.TestCase):
    def test_doi_filter(self):
        doi_fn = partial( doi_urls, lambda x: x)

        s = ''
        self.assertEqual(doi_fn(s), s)

        s = 'some test string 23$6#$5&456 http://google.com/notadoi'
        self.assertEqual( doi_fn(s), s)

        doi = '10.1103/PhysRevD.76.013009'
        doiurl = doi_fn(doi)
        self.assertRegex(doiurl, r'^<a', 'should start with a tag')
        self.assertEqual(doiurl,
                         '<a href="https://dx.doi.org/10.1103%2FPhysRevD.76.013009">10.1103/PhysRevD.76.013009</a>')

        s = f'something something {doi} endthing'
        doiurl = doi_fn(s)
        self.assertRegex(doiurl, r'<a href=', 'Have an A tag')
        self.assertRegex(doiurl, '^something something ')
        self.assertRegex(doiurl, ' endthing$')

    def test_arxiv_id_urls_basic(self):
        #Totally bogus setup for testing this so at least url_for returns something
        h='sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(arxiv_id_urls(''), equal_to(''))
            s = 'some text 134#%$$%&^^%*^&(()*_)_<>?:;[}}'
            assert_that(arxiv_id_urls(s), equal_to(s))
            assert_that(
                arxiv_id_urls('hep-th/9901001'),
                equal_to(f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a>',),
            )
            assert_that(
                arxiv_id_urls('hep-th/9901001 hep-th/9901002'),
                equal_to(f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>'),
            )


    def test_arxiv_id_urls_3(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(
                arxiv_id_urls('hep-th/9901002'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>', )
            )
            assert_that(
                arxiv_id_urls('hep-th/9901002\n'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>\n', ),
            )
            assert_that(
                arxiv_id_urls('arXiv:dg-ga/9401001 hep-th/9901001 hep-th/9901002'),
                equal_to(f'<a href="http://{h}/abs/dg-ga/9401001">arXiv:dg-ga/9401001</a> <a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>',),
            )

    def test_arxiv_id_urls_punct(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(
                arxiv_id_urls('hep-th/9901002.'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>.', ),
                'followed by period'
            )
            assert_that(
                arxiv_id_urls('0702.0003.'),
                equal_to(
                    f'<a href="http://{h}/abs/0702.0003">0702.0003</a>.', ),
                'followed by period'
            )
            assert_that(
                arxiv_id_urls('hep-th/9901001,hep-th/9901002'),
                equal_to(f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a>,<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>'),
                'filter_urls_ids_escape (ID linking) 3/7'
            )
            assert_that(
                arxiv_id_urls('0702.0003, something'),
                equal_to(
                    f'<a href="http://{h}/abs/0702.0003">0702.0003</a>, something', ),
                'followed by comma'
            )
            assert_that(
                arxiv_id_urls('(0702.0003) something'),
                equal_to(
                    f'(<a href="http://{h}/abs/0702.0003">0702.0003</a>) something', ),
                'in parens'
            )

    def test_arxiv_id_urls_more(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(
                arxiv_id_urls('arXiv:dg-ga/9401001 hep-th/9901001 0704.0001'),
                f'<a href="http://{h}/abs/dg-ga/9401001">arXiv:dg-ga/9401001</a> <a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/0704.0001">0704.0001</a>',
                'filter_urls_ids_escape (ID linking) 5/7'
            )


    def test_arxiv_id_v(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            self.assertEqual(
                arxiv_id_urls('arXiv:dg-ga/9401001v12 hep-th/9901001v2 0704.0001v1'),
                f'<a href="http://{h}/abs/dg-ga/9401001v12">arXiv:dg-ga/9401001v12</a> <a href="http://{h}/abs/hep-th/9901001v2">hep-th/9901001v2</a> <a href="http://{h}/abs/0704.0001v1">0704.0001v1</a>',
                'arxiv ids with version numbers'
            )

    def test_vixra(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(
                arxiv_id_urls('viXra:0704.0001 viXra:1003.0123'),
                'viXra:0704.0001 viXra:1003.0123',
                'filter_urls_ids_escape (ID linking) 6/7'
            )
            self.assertEqual(
                arxiv_id_urls('vixra:0704.0001'),
                f'vixra:<a href="http://{h}/abs/0704.0001">0704.0001</a>',
                'filter_urls_ids_escape (ID linking) 7/7'
            )