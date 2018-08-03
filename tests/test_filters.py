from hamcrest import *
import unittest
from functools import partial

from jinja2 import escape, Markup, Environment
from jinja2.utils import urlize

from app import app
from browse.filters import doi_urls, arxiv_id_urls, line_feed_to_br


class Jinja_Custom_Fitlers_Test(unittest.TestCase):
    def test_with_jinja(self):
        jenv= Environment(autoescape=True)
        jenv.filters['doi_urls'] = partial(doi_urls, lambda x:x)
        assert_that( jenv.from_string( '{{"something 10.1103/PhysRevD.76.013009 or other"|doi_urls}}').render(),
                     equal_to( 'something <a href="https://dx.doi.org/10.1103%2FPhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> or other' ))

    def test_with_jinja_escapes(self):
        jenv = Environment(autoescape=True)
        jenv.filters['doi_urls'] = partial(doi_urls, lambda x: x)
        assert_that(jenv.from_string('{{"something 10.1103/PhysRevD.76.013009 or other"|doi_urls}}').render(),
                        equal_to(
                            'something <a href="https://dx.doi.org/10.1103%2FPhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> or other'))

        assert_that( jenv.from_string('{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009"|urlize}}').render(),
                     equal_to('&lt;script&gt;bad junk&lt;/script&gt; something 10.1103/PhysRevD.76.013009'))

        assert_that( jenv.from_string( '{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009 or other"|urlize|doi_urls}}').render(),
                     equal_to( '&lt;script&gt;bad junk&lt;/script&gt; something <a href="https://dx.doi.org/10.1103%2FPhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> or other' ),
                     'should not double escape')


    def test_doi_filter(self):
        doi_fn = partial( doi_urls, lambda x: x)

        s = ''
        self.assertEqual(doi_fn(s), s)

        s = 'some test string 23$6#$5<>&456 http://google.com/notadoi'
        assert_that(doi_fn(s), equal_to(escape(s)))
        assert_that(doi_fn(s), equal_to(escape(doi_fn(s))))

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

        txt = '10.1103/PhysRevA.99.013009 10.1103/PhysRevZ.44.023009 10.1103/PhysRevX.90.012309 10.1103/BioRevX.44.123456'
        assert_that(doi_fn(txt),
                    equal_to(Markup('<a href="https://dx.doi.org/10.1103%2FPhysRevA.99.013009">10.1103/PhysRevA.99.013009</a>'\
                                    ' <a href="https://dx.doi.org/10.1103%2FPhysRevZ.44.023009">10.1103/PhysRevZ.44.023009</a>'\
                                    ' <a href="https://dx.doi.org/10.1103%2FPhysRevX.90.012309">10.1103/PhysRevX.90.012309</a>'\
                                    ' <a href="https://dx.doi.org/10.1103%2FBioRevX.44.123456">10.1103/BioRevX.44.123456</a>')))

        mkup = urlize( txt )
        assert_that(doi_fn(mkup),
                    equal_to(Markup(
                        '<a href="https://dx.doi.org/10.1103%2FPhysRevA.99.013009">10.1103/PhysRevA.99.013009</a>' \
                        ' <a href="https://dx.doi.org/10.1103%2FPhysRevZ.44.023009">10.1103/PhysRevZ.44.023009</a>' \
                        ' <a href="https://dx.doi.org/10.1103%2FPhysRevX.90.012309">10.1103/PhysRevX.90.012309</a>' \
                        ' <a href="https://dx.doi.org/10.1103%2FBioRevX.44.123456">10.1103/BioRevX.44.123456</a>')))

        txt = '<script>Im from the user and Im bad</script>'
        assert_that(doi_fn( f'{doi} {txt}'),
                    equal_to( f'<a href="https://dx.doi.org/10.1103%2FPhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> {escape(txt)}' ))

    def test_arxiv_id_urls_basic(self):
        h = 'sosmooth.org'  # Totally bogus setup for testing, at least url_for returns something
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(arxiv_id_urls(''), equal_to(''))
            s = 'some text 134#%$$%&^^%*^&(()*_)_<>?:;[}}'
            assert_that(arxiv_id_urls(s), equal_to(escape(s)),
                        'filers should return marked up text, which means its escaped')
            assert_that(
                arxiv_id_urls('hep-th/9901001'),
                equal_to(f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a>',))
            assert_that(
                arxiv_id_urls('hep-th/9901001 hep-th/9901002'),
                equal_to(f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>'))

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
            assert_that(arxiv_id_urls('arXiv:dg-ga/9401001v12 hep-th/9901001v2 0704.0001v1'),
                equal_to(f'<a href="http://{h}/abs/dg-ga/9401001v12">arXiv:dg-ga/9401001v12</a> <a href="http://{h}/abs/hep-th/9901001v2">hep-th/9901001v2</a> <a href="http://{h}/abs/0704.0001v1">0704.0001v1</a>'),
                'arxiv ids with version numbers' )

    def test_vixra(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(
                arxiv_id_urls('viXra:0704.0001 viXra:1003.0123'),
                equal_to('viXra:0704.0001 viXra:1003.0123'))

            # this is what was expected in legacy, but it doesn't seem right:
            # assert_that(
            #     arxiv_id_urls('vixra:0704.0001'),
            #     equal_to(f'vixra:<a href="http://{h}/abs/0704.0001">0704.0001</a>'))

    def test_arxiv_id_urls_escaping(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            ax_id = 'hep-th/9901002'

            user_entered_txt=' <div>div should be escaped</div>'
            ex_txt = escape(user_entered_txt).__html__()
            assert_that(
                arxiv_id_urls(ax_id + user_entered_txt),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>{ex_txt}'),
                    'Dealing with user entered text with html that should be escaped for safety')

            jinja_escaped_txt = Markup(' <div>div should already be escaped by jinja2</div>')
            assert_that(
                arxiv_id_urls(ax_id + jinja_escaped_txt),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>{jinja_escaped_txt}'),
                    'Dealing with text that has been escaped by Jinja2 already')


    def test_arxiv_id_jinja_escapes(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():

            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_id_urls'] = arxiv_id_urls

            assert_that(jenv.from_string('{{"something hep-th/9901002 or other"|arxiv_id_urls}}').render(),
                        equal_to(
                            f'something <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a> or other'))

            assert_that(
                jenv.from_string('{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009"|urlize}}').render(),
                equal_to('&lt;script&gt;bad junk&lt;/script&gt; something 10.1103/PhysRevD.76.013009'))

            assert_that(jenv.from_string(
                '{{"<script>bad junk</script> http://google.com something or '\
                'hep-th/9901002 other"|urlize|arxiv_id_urls}}').render(),
                equal_to(
                            '&lt;script&gt;bad junk&lt;/script&gt; '\
                            '<a href="http://google.com" rel="noopener">http://google.com</a> something or '\
                            f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a> other'),
                        'should not double escape')

    def test_line_break(self):
        assert_that(line_feed_to_br('blal\n  bla'), equal_to('blal\n<br />bla'))

        assert_that(line_feed_to_br('\nblal\n  bla'), equal_to('\nblal\n<br />bla'))

        assert_that(line_feed_to_br('\n blal\n  bla'), equal_to('\n blal\n<br />bla'), 'need to not do <br /> on first line')
        assert_that(line_feed_to_br('blal\n\nbla'), equal_to('blal\nbla'), 'skip blank lines')

    def test_line_brake_jinja(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_id_urls'] = arxiv_id_urls
            jenv.filters['line_brake'] = line_feed_to_br
            jenv.filters['doi_urls'] = partial(doi_urls, lambda x: x)

            assert_that(jenv.from_string(
                '{{" <script>bad junk</script> http://google.com something or \n' \
                '\n'
                'no double \\n'
                ' should have br\n'
                'hep-th/9901002 other"|urlize|line_brake|arxiv_id_urls}}').render(),
                equal_to(
                    ' &lt;script&gt;bad junk&lt;/script&gt; '\
                    '<a href="http://google.com" rel="noopener">http://google.com</a>'\
                    ' something or \n'\
                    'no double \n'\
                    '<br />should have br\n'\
                    '<a href="http://sosmooth.org/abs/hep-th/9901002">hep-th/9901002</a> other'),
                    'urlize, line_brake and arxiv_id_urls should all work together')