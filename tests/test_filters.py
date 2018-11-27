import unittest
from hamcrest import *
from functools import partial

from jinja2 import escape, Markup, Environment

from flask import appcontext_pushed, url_for
from app import app

from browse.filters import line_feed_to_br, tex_to_utf, entity_to_utf
from browse.util.id_patterns import do_dois_to_tags, do_dois_id_urls_to_tags,\
    do_id_to_tags


def _id_to_url(id: str):
    return url_for('browse.abstract', arxiv_id=id)
    
def arxiv_urlize(txt):
    return do_dois_id_urls_to_tags(_id_to_url,None,txt)

def doi_urls(fn, txt):
    return do_dois_to_tags(fn, txt)

def arxiv_id_urls(txt):
    return do_id_to_tags(_id_to_url, txt)

class Jinja_Custom_Fitlers_Test(unittest.TestCase):
    def test_with_jinja(self):
        jenv = Environment(autoescape=True)
        jenv.filters['doi_urls'] = partial(doi_urls, lambda x: x)
        assert_that(
            jenv.from_string(
                '{{"something 10.1103/PhysRevD.76.013009 or other"|doi_urls}}'
            ).render(),
            equal_to(
                'something <a href="https://dx.doi.org/10.1103/PhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> or other'
            ))

    def test_with_jinja_escapes(self):
        jenv = Environment(autoescape=True)
        jenv.filters['doi_urls'] = partial(doi_urls, lambda x: x)
        jenv.filters['arxiv_urlize'] = arxiv_urlize
        assert_that(
            jenv.from_string(
                '{{"something 10.1103/PhysRevD.76.013009 or other"|doi_urls}}'
            ).render(),
            equal_to(
                'something <a href="https://dx.doi.org/10.1103/PhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> or other'
            ))

        assert_that(
            jenv.from_string(
                '{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009"|arxiv_urlize}}'
            ).render(),
            equal_to(
                '&lt;script&gt;bad junk&lt;/script&gt; something <a href="https://dx.doi.org/10.1103/PhysRevD.76.013009">10.1103/PhysRevD.76.013009</a>'
            ))

    def test_doi_filter(self):
        doi_fn = partial(doi_urls, lambda x: x)

        s = ''
        self.assertEqual(doi_fn(s), s)

        s = 'some test string 23$6#$5<>&456 http://google.com/notadoi'
        assert_that(doi_fn(s), equal_to(escape(s)))

        doi = '10.1103/PhysRevD.76.013009'
        doiurl = doi_fn(doi)
        self.assertRegex(doiurl, r'^<a', 'should start with a tag')
        assert_that(doiurl,
                    equal_to(
                        Markup('<a href="https://dx.doi.org/10.1103/PhysRevD.76.013009">10.1103/PhysRevD.76.013009</a>')))

        s = f'something something {doi} endthing'
        doiurl = doi_fn(s)
        self.assertRegex(doiurl, r'<a href=', 'Have an A tag')
        self.assertRegex(doiurl, '^something something ')
        self.assertRegex(doiurl, ' endthing$')

        txt = '10.1103/PhysRevA.99.013009 10.1103/PhysRevZ.44.023009 10.1103/PhysRevX.90.012309 10.1103/BioRevX.44.123456'
        assert_that(
            doi_fn(txt),
            equal_to(
                Markup(
                    '<a href="https://dx.doi.org/10.1103/PhysRevA.99.013009">10.1103/PhysRevA.99.013009</a>'
                    ' <a href="https://dx.doi.org/10.1103/PhysRevZ.44.023009">10.1103/PhysRevZ.44.023009</a>'
                    ' <a href="https://dx.doi.org/10.1103/PhysRevX.90.012309">10.1103/PhysRevX.90.012309</a>'
                    ' <a href="https://dx.doi.org/10.1103/BioRevX.44.123456">10.1103/BioRevX.44.123456</a>'
                )))

        txt = '<script>Im from the user and Im bad</script>'
        assert_that(
            doi_fn(f'{doi} {txt}'),
            equal_to(
                Markup(f'<a href="https://dx.doi.org/10.1103/PhysRevD.76.013009">10.1103/PhysRevD.76.013009</a> {escape(txt)}')
            ))

    def test_arxiv_id_urls_basic(self):
        h = 'sosmooth.org'  # Totally bogus setup for testing, at least url_for returns something
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(arxiv_id_urls(''), equal_to(''))
            s = 'some text 134#%$$%&^^%*^&(()*_)_<>?:;[}}'
            assert_that(
                arxiv_id_urls(s), equal_to(escape(s)),
                'filers should return marked up text, which means its escaped')
            assert_that(
                arxiv_id_urls('hep-th/9901001'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a>',
                ))
            assert_that(
                arxiv_id_urls('hep-th/9901001 hep-th/9901002'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>'
                ))

    def test_arxiv_id_urls_3(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(
                arxiv_id_urls('hep-th/9901002'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>',
                ))
            assert_that(
                arxiv_id_urls('hep-th/9901002\n'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>\n',
                ),
            )
            assert_that(
                arxiv_id_urls(
                    'arXiv:dg-ga/9401001 hep-th/9901001 hep-th/9901002'),
                equal_to(
                    f'<a href="http://{h}/abs/dg-ga/9401001">arXiv:dg-ga/9401001</a> <a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>',
                ),
            )

    def test_arxiv_id_urls_punct(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            assert_that(
                arxiv_id_urls('hep-th/9901002.'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>.',
                ), 'followed by period')
            assert_that(
                arxiv_id_urls('0702.0003.'),
                equal_to(
                    f'<a href="http://{h}/abs/0702.0003">0702.0003</a>.', ),
                'followed by period')
            assert_that(
                arxiv_id_urls('hep-th/9901001,hep-th/9901002'),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a>,<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>'
                ), 'filter_urls_ids_escape (ID linking) 3/7')
            assert_that(
                arxiv_id_urls('0702.0003, something'),
                equal_to(
                    f'<a href="http://{h}/abs/0702.0003">0702.0003</a>, something',
                ), 'followed by comma')
            assert_that(
                arxiv_id_urls('(0702.0003) something'),
                equal_to(
                    f'(<a href="http://{h}/abs/0702.0003">0702.0003</a>) something',
                ), 'in parens')

    def test_arxiv_id_urls_more(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(
                arxiv_id_urls('arXiv:dg-ga/9401001 hep-th/9901001 0704.0001'),
                f'<a href="http://{h}/abs/dg-ga/9401001">arXiv:dg-ga/9401001</a> <a href="http://{h}/abs/hep-th/9901001">hep-th/9901001</a> <a href="http://{h}/abs/0704.0001">0704.0001</a>',
                'filter_urls_ids_escape (ID linking) 5/7')

    def test_arxiv_id_v(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            assert_that(
                arxiv_id_urls(
                    'arXiv:dg-ga/9401001v12 hep-th/9901001v2 0704.0001v1'),
                equal_to(
                    f'<a href="http://{h}/abs/dg-ga/9401001v12">arXiv:dg-ga/9401001v12</a> <a href="http://{h}/abs/hep-th/9901001v2">hep-th/9901001v2</a> <a href="http://{h}/abs/0704.0001v1">0704.0001v1</a>'
                ), 'arxiv ids with version numbers')

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

            user_entered_txt = ' <div>div should be escaped</div>'
            ex_txt = escape(user_entered_txt).__html__()
            assert_that(
                arxiv_id_urls(ax_id + user_entered_txt),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>{ex_txt}'
                ),
                'Dealing with user entered text with html that should be escaped for safety'
            )

            jinja_escaped_txt = Markup(
                ' <div>div should already be escaped by jinja2</div>')
            assert_that(
                arxiv_id_urls(ax_id + jinja_escaped_txt),
                equal_to(
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a>{jinja_escaped_txt}'
                ), 'Dealing with text that has been escaped by Jinja2 already')

    def test_arxiv_id_jinja_escapes(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():

            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_id_urls'] = arxiv_id_urls
            jenv.filters['arxiv_urlize'] = arxiv_urlize

            assert_that(
                jenv.from_string(
                    '{{"something hep-th/9901002 or other"|arxiv_id_urls}}').
                render(),
                equal_to(
                    f'something <a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a> or other'
                ))

            assert_that(
                jenv.from_string(
                    '{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009"|arxiv_urlize}}'
                ).render(),
                equal_to(
                    '&lt;script&gt;bad junk&lt;/script&gt; something <a href="https://dx.doi.org/10.1103/PhysRevD.76.013009">10.1103/PhysRevD.76.013009</a>'
                ))

            assert_that(
                jenv.from_string(
                    '{{"<script>bad junk</script> http://google.com bla bla '
                    'hep-th/9901002 bla"|arxiv_urlize}}').
                render(),
                equal_to(
                    '&lt;script&gt;bad junk&lt;/script&gt; '
                    '<a href="http://google.com">this http URL</a> bla bla '
                    f'<a href="http://{h}/abs/hep-th/9901002">hep-th/9901002</a> bla'
                ), 'should not double escape')

    def test_line_break(self):
        assert_that(
            line_feed_to_br('blal\n  bla'), equal_to('blal\n<br />bla'))

        assert_that(
            line_feed_to_br('\nblal\n  bla'), equal_to('\nblal\n<br />bla'))

        assert_that(
            line_feed_to_br('\n blal\n  bla'), equal_to('\n blal\n<br />bla'),
            'need to not do <br /> on first line')
        assert_that(
            line_feed_to_br('blal\n\nbla'), equal_to('blal\nbla'),
            'skip blank lines')

    def test_line_break_jinja(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_urlize'] = arxiv_urlize
            jenv.filters['line_break'] = line_feed_to_br

            assert_that(
                jenv.from_string(
                    '{{"<script>bad junk</script> http://google.com something or \n'
                    '\n'
                    'no double \\n'
                    ' should have br\n'
                    'hep-th/9901002 other"|line_break|arxiv_urlize}}'
                ).render(),
                equal_to(
                    '&lt;script&gt;bad junk&lt;/script&gt; '
                    '<a href="http://google.com">this http URL</a>'
                    ' something or \n'
                    'no double \n'
                    '<br />should have br\n'
                    '<a href="http://sosmooth.org/abs/hep-th/9901002">hep-th/9901002</a> other'
                ),
                'line_break and arxiv_id_urls should work together'
            )

    def test_tex_to_utf(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_id_urls'] = arxiv_id_urls
            jenv.filters['line_break'] = line_feed_to_br
            jenv.filters['doi_urls'] = partial(doi_urls, lambda x: x)
            jenv.filters['arxiv_urlize'] = arxiv_urlize
            jenv.filters['tex_to_utf'] = tex_to_utf

            assert_that(
                jenv.from_string('{{""|tex_to_utf|arxiv_id_urls}}').render(),
                equal_to(''))

            title = jenv.from_string(
                '{{"Finite-Size and Finite-Temperature Effects in the Conformally Invariant O(N) Vector Model for 2<d<4"|tex_to_utf|arxiv_id_urls}}'
            ).render()
            assert_that(
                title,
                equal_to(
                    'Finite-Size and Finite-Temperature Effects in the Conformally Invariant O(N) Vector Model for 2&lt;d&lt;4'
                ),
                'tex_to_utf and arxiv_id_urls should handle < and > ARXIVNG-1227'
            )

            assert_that(tex_to_utf('Lu\\\'i'), equal_to('Luí'))
            assert_that(tex_to_utf(Markup('Lu\\\'i')), equal_to('Luí'))
            assert_that(tex_to_utf(Markup(escape('Lu\\\'i'))), equal_to('Luí'))

    def test_entity_to_utf(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_id_urls'] = arxiv_id_urls
            jenv.filters['line_break'] = line_feed_to_br
            jenv.filters['doi_urls'] = partial(doi_urls, lambda x: x)
            jenv.filters['arxiv_urlize'] = arxiv_urlize
            jenv.filters['tex_to_utf'] = tex_to_utf
            jenv.filters['entity_to_utf'] = entity_to_utf
            assert_that(
                jenv.from_string('{{ "Mart&#xED;n"|entity_to_utf }}').render(),
                equal_to('Martín'), 'entity_to_utf should work')
            assert_that(
                jenv.from_string(
                    '{{ "<Mart&#xED;n>"|entity_to_utf }}').render(),
                equal_to('&lt;Martín&gt;'),
                'entity_to_utf should work even with < or >')

    def test_arxiv_urlize_no_email_links(self):
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['arxiv_urlize'] = arxiv_urlize

            assert_that(
                jenv.from_string(
                    '{{ "bob@example.com"|arxiv_urlize }}').render(),
                equal_to('bob@example.com'),
                'arxiv_urlize should not turn emails into links')
            assert_that(
                jenv.from_string(
                    '{{ "<bob@example.com>"|arxiv_urlize }}').render(),
                equal_to('&lt;bob@example.com&gt;'),
                'arxiv_urlize should work even with < or >')

    def test_arxiv_urlize(self):



        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():

            def do_arxiv_urlize(txt):
                return arxiv_urlize(txt)
            
            self.assertEqual(
                do_arxiv_urlize('http://example.com/'),
                '<a href="http://example.com/">this http URL</a>',
                'do_arxiv_urlize (URL linking) 1/6')
            self.assertEqual(
                do_arxiv_urlize('https://example.com/'),
                '<a href="https://example.com/">this https URL</a>',
                'do_arxiv_urlize (URL linking) 2/6')
            self.assertEqual(
                do_arxiv_urlize('ftp://example.com/'),
                '<a href="ftp://example.com/">this ftp URL</a>',
                'do_arxiv_urlize (URL linking) 3/6')
            self.assertEqual(
                do_arxiv_urlize('http://example.com/.hep-th/9901001'),
                '<a href="http://example.com/.hep-th/9901001">this http URL</a>',
                'do_arxiv_urlize (URL linking) 4/6')
            self.assertEqual(
                do_arxiv_urlize(
                    'http://projecteuclid.org/euclid.bj/1151525136'
                ),
                '<a href="http://projecteuclid.org/euclid.bj/1151525136">this http URL</a>',
                'do_arxiv_urlize (URL linking) 6/6')
            assert_that(
                do_arxiv_urlize('  Correction to Bernoulli (2006), 12, 551--570 http://projecteuclid.org/euclid.bj/1151525136'),
                equal_to(Markup('  Correction to Bernoulli (2006), 12, 551--570 <a href="http://projecteuclid.org/euclid.bj/1151525136">this http URL</a>')),
                'do_arxiv_urlize (URL linking) 6/6')
            # shouldn't match
            self.assertEqual(
                do_arxiv_urlize('2448446.4710(5)'), '2448446.4710(5)',
                'do_arxiv_urlize (should not match) 1/9')
            self.assertEqual(
                do_arxiv_urlize('HJD=2450274.4156+/-0.0009'),
                'HJD=2450274.4156+/-0.0009',
                'do_arxiv_urlize (should not match) 2/9')
            self.assertEqual(
                do_arxiv_urlize('T_min[HJD]=49238.83662(14)+0.146352739(11)E.'),
                'T_min[HJD]=49238.83662(14)+0.146352739(11)E.',
                'do_arxiv_urlize (should not match) 3/9')
            self.assertEqual(
                do_arxiv_urlize('Pspin=1008.3408s'), 'Pspin=1008.3408s',
                'do_arxiv_urlize (should not match) 4/9')
            self.assertEqual(
                do_arxiv_urlize('2453527.87455^{+0.00085}_{-0.00091}'),
                '2453527.87455^{+0.00085}_{-0.00091}',
                'do_arxiv_urlize (should not match) 5/9')
            self.assertEqual(
                do_arxiv_urlize('2451435.4353'), '2451435.4353',
                'do_arxiv_urlize (should not match) 6/9')
            assert_that(
                do_arxiv_urlize('cond-mat/97063007'),
                equal_to('<a href="http://sosmooth.org/abs/cond-mat/9706300">cond-mat/9706300</a>7'),
                'do_arxiv_urlize (should match) 7/9')
            
            assert_that(
                do_arxiv_urlize('[http://onion.com/something-funny-about-arxiv-1234]'),
                equal_to('[<a href="http://onion.com/something-funny-about-arxiv-1234">this http URL</a>]'))
            
            assert_that(
                do_arxiv_urlize('[http://onion.com/?q=something-funny-about-arxiv.1234]'),
                equal_to('[<a href="http://onion.com/?q=something-funny-about-arxiv.1234">this http URL</a>]'))
            
            assert_that(
                do_arxiv_urlize('http://onion.com/?q=something funny'),
                equal_to('<a href="http://onion.com/?q=something">this http URL</a> funny'),
                'Spaces CANNOT be expected to be part of URLs')
            
            assert_that(
                do_arxiv_urlize('"http://onion.com/something-funny-about-arxiv-1234"'),
                equal_to(Markup('&#34;<a href="http://onion.com/something-funny-about-arxiv-1234">this http URL</a>&#34;')),
                'Should handle URL surrounded by double quotes')

