from hamcrest import *
import unittest
import re

from jinja2 import Markup, escape
from browse.util.id_patterns import _find_match, Matchable, dois_ids_and_urls, \
 _transform_token, do_dois_id_urls_to_tags


class Id_Patterns_Test(unittest.TestCase):

    def test_basic(self):
        _find_match([], 'test')

        m = _find_match( [Matchable([], re.compile(r'test'))], 'test')
        assert_that(m, is_not(None))

        m0 = Matchable([], re.compile(r'test'))
        m1 = Matchable([], re.compile(r'tests'))

        m = _find_match( [m0, m1], 'test')
        assert_that(m, is_not(None))
        assert_that(m[1], equal_to(m0))

        m = _find_match([m0, m1], 'tests')
        assert_that(m, is_not(None))
        assert_that(m[1], equal_to(m0))

        m = _find_match([m1, m0], 'tests')
        assert_that(m, is_not(None))
        assert_that(m[1], equal_to(m1))

    def test_arxiv_ids(self):
        def find_match(txt):
            return _find_match(dois_ids_and_urls, txt)
        
        assert_that(find_match('math/9901123'), is_not(None))
        assert_that(find_match('hep-ex/9901123'), is_not(None))
        assert_that(find_match('gr-qc/9901123'), is_not(None))

        assert_that(find_match('1202.1234'), is_not(None))
        assert_that(find_match('1202.1234v1'), is_not(None))
        assert_that(find_match('1203.12345'), is_not(None))
        assert_that(find_match('1203.12345v1'), is_not(None))
        assert_that(find_match('1203.12345v12'), is_not(None))

        # slightly odd but seen in comments
        assert_that(find_match('hep-ph/1203.12345v12'), is_not(None))

    def test_find_match(self):
        def find_match(txt):
            return _find_match(dois_ids_and_urls, txt)

        assert_that(find_match('junk'), equal_to(None))
        assert_that(find_match(''), equal_to(None))
        assert_that(find_match(' '), equal_to(None))

        assert_that(find_match('doi:10.1002/0470841559.ch1'), is_not(None))
        assert_that(find_match('doi:10.1038/nphys1170'), is_not(None))

        assert_that(find_match('http://arxiv.org'), is_not(None))
        assert_that(find_match('http://arxiv.org?something=1'), is_not(None))
        assert_that(find_match(
            'http://arxiv.org?something=1&anohter=2'), is_not(None))
        assert_that(find_match('"http://arxiv.org"'), is_not(None))

    def test_transform_token(self):
        # def doi_id_url_transform_token(tkn,fn):
        #     return doi_id_url_transform_token(fn, tkn)
        
        assert_that(
            do_dois_id_urls_to_tags( None, ''),
            equal_to(''))
        
        assert_that(
            do_dois_id_urls_to_tags( None, 
                     'it is fine, chapter 234 see<xxyx,234>'),
            equal_to(Markup(escape('it is fine, chapter 234 see<xxyx,234>'))))

        assert_that(
            do_dois_id_urls_to_tags( None, 'http://arxiv.org'),
            equal_to('<a href="http://arxiv.org">this http URL</a>'))

        assert_that(
            do_dois_id_urls_to_tags( None, 
                'Stuff in the front http://arxiv.org other stuff'),
            equal_to('Stuff in the front <a href="http://arxiv.org">this http URL</a> other stuff'))

        assert_that(
            do_dois_id_urls_to_tags( None, '.http://arxiv.org.'),
            equal_to('.<a href="http://arxiv.org">this http URL</a>.'))

        assert_that(
            do_dois_id_urls_to_tags( None, '"http://arxiv.org"'),
            equal_to(Markup('&#34;<a href="http://arxiv.org">this http URL</a>&#34;')))

    def test_urlize(self):
        def do_arxiv_urlize(txt):
            return do_dois_id_urls_to_tags(lambda x: x, txt)

        assert_that(
            do_arxiv_urlize('http://example.com/'),
            equal_to('<a href="http://example.com/">this http URL</a>'),
            'do_arxiv_urlize (URL linking) 1/6')
        assert_that(
            do_arxiv_urlize('https://example.com/'),
            equal_to('<a href="https://example.com/">this https URL</a>'),
            'do_arxiv_urlize (URL linking) 2/6')
        assert_that(
            do_arxiv_urlize('ftp://example.com/'),
            equal_to('<a href="ftp://example.com/">this ftp URL</a>'),
            'do_arxiv_urlize (URL linking) 3/6')
        

        assert_that(
            do_arxiv_urlize(
                'http://projecteuclid.org/euclid.bj/1151525136'
            ),
            equal_to('<a href="http://projecteuclid.org/euclid.bj/1151525136">this http URL</a>'),
            'do_arxiv_urlize (URL linking) 6/6')
        # assert_that(
        #     do_arxiv_urlize(
        #         '  Correction to Bernoulli (2006), 12, 551--570 http://projecteuclid.org/euclid.bj/1151525136'),
        #     equal_to(
        #         '  Correction to Bernoulli (2006), 12, 551--570 <a href="http://projecteuclid.org/euclid.bj/1151525136">this http URL</a>'),
        #     'do_arxiv_urlize (URL linking) 6/6')
        # shouldn't match
        assert_that(
            do_arxiv_urlize('2448446.4710(5)'), '2448446.4710(5)',
        equal_to('do_arxiv_urlize (should not match) 1/9'))
        self.assertEqual(
            do_arxiv_urlize('HJD=2450274.4156+/-0.0009'),
            'HJD=2450274.4156+/-0.0009',
            'do_arxiv_urlize (should not match) 2/9')
        assert_that(
            do_arxiv_urlize(
                'T_min[HJD]=49238.83662(14)+0.146352739(11)E.'),
            equal_to('T_min[HJD]=49238.83662(14)+0.146352739(11)E.'),
            'do_arxiv_urlize (should not match) 3/9')
        assert_that(
            do_arxiv_urlize('Pspin=1008.3408s'), 'Pspin=1008.3408s',
        equal_to('do_arxiv_urlize (should not match) 4/9'))
        assert_that(
            do_arxiv_urlize('2453527.87455^{+0.00085}_{-0.00091}'),
            equal_to('2453527.87455^{+0.00085}_{-0.00091}'),
            'do_arxiv_urlize (should not match) 5/9')
        assert_that(
            do_arxiv_urlize('2451435.4353'), equal_to('2451435.4353'),
        'do_arxiv_urlize (should not match) 6/9')

        
        assert_that(
            do_arxiv_urlize('cond-mat/97063007'),
            equal_to(
                '<a href="cond-mat/9706300">cond-mat/9706300</a>7'),
            'do_arxiv_urlize (should match) 7/9')

        assert_that(
            do_arxiv_urlize(
                '[http://onion.com/something-funny-about-arxiv-1234]'),
            equal_to('[<a href="http://onion.com/something-funny-about-arxiv-1234">this http URL</a>]'))

        assert_that(
            do_arxiv_urlize(
                '[http://onion.com/?q=something-funny-about-arxiv.1234]'),
            equal_to('[<a href="http://onion.com/?q=something-funny-about-arxiv.1234">this http URL</a>]'))

        assert_that(
            do_arxiv_urlize('http://onion.com/?q=something funny'),
            equal_to(
                '<a href="http://onion.com/?q=something">this http URL</a> funny'),
            'Spaces CANNOT be expected to be part of URLs')

        assert_that(
            do_arxiv_urlize(
                '"http://onion.com/something-funny-about-arxiv-1234"'),
            equal_to(
                Markup('&#34;<a href="http://onion.com/something-funny-about-arxiv-1234">this http URL</a>&#34;')),
            'Should handle URL surrounded by double quotes')
        
        assert_that(
            do_arxiv_urlize('< http://example.com/1<2 ><'),
            equal_to('&lt; <a href="http://example.com/1">this http URL</a>&lt;2 &gt;&lt;'),
            'do_arxiv_urlize (URL linking) 5/6')

        assert_that(
            do_arxiv_urlize('Accepted for publication in A&A. The data will be available via CDS, and can be found "http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_FILAMENTS.cgi"'),
            equal_to('Accepted for publication in A&amp;A. The data will be available via CDS, and can be found &#34;<a href=\"http://atlasgal.mpifr-bonn.mpg.de/cgi-bin/ATLASGAL_FILAMENTS.cgi">this http URL</a>&#34;')
            )

        assert_that(
            do_arxiv_urlize('see http://www.tandfonline.com/doi/abs/doi:10.1080/15980316.2013.860928?journalCode=tjid20'),
            equal_to('see <a href="http://www.tandfonline.com/doi/abs/doi:10.1080/15980316.2013.860928?journalCode=tjid20">this http URL</a>')
        )

        assert_that(
            do_arxiv_urlize('http://authors.elsevier.com/a/1TcSd,Ig45ZtO'),
            equal_to('<a href="http://authors.elsevier.com/a/1TcSd,Ig45ZtO">this http URL</a>'))
        
    def category_id_test(self):
        def do_arxiv_urlize(txt):
            return do_dois_id_urls_to_tags(lambda x: x, txt)
        
        assert_that(
            do_arxiv_urlize('version of arXiv.math.GR/0512484 (2011).'),
            equal_to('version of arXiv.<a href=\"math.GR/0512484\">math.GR/0512484</a> (2011).'))

    def hosts_tests(self):
        def do_arxiv_urlize(txt):
            return do_dois_id_urls_to_tags(lambda x: x, txt)
        
        assert_that(do_arxiv_urlize('can be downloaded from http://rwcc.bao.ac.cn:8001/swap/NLFFF_DBIE_code/HeHan_NLFFF_JGR.pdf'),
                    equal_to("can be downloaded from <a href=\"http://rwcc.bao.ac.cn:8001/swap/NLFFF_DBIE_code/HeHan_NLFFF_JGR.pdf\">this http URL</a>"),
                    "Should deal with ports correctly")


        assert_that(do_arxiv_urlize("images is at http://85.20.11.14/hosting/punsly/APJLetter4.2.07/"),
                    equal_to('images is at <a href="http://85.20.11.14/hosting/punsly/APJLetter4.2.07/">this http URL</a>'),
                    "should deal with numeric IP correctly")
