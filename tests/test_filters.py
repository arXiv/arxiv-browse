import unittest
from functools import partial

from jinja2 import escape, Markup, Environment

from flask import appcontext_pushed, url_for
from app import app

from arxiv.base.urls import links, urlizer, urlize
from arxiv.base.filters import abstract_lf_to_br, f_tex2utf
from browse.filters import entity_to_utf


class Jinja_Custom_Filters_Test(unittest.TestCase):
    """Browse jinja filter tests."""

    def test_with_jinja(self):
        """Basic urlize DOI filter test."""
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['urlize'] = urlizer(
                ['doi']
            )
            self.assertEqual(
                jenv.from_string(
                    '{{"something 10.1103/PhysRevD.76.013009 or other"|urlize}}'
                ).render(),
                'something &lt;a class=&#34;link-https&#34; data-doi=&#34;10.1103/PhysRevD.76.013009&#34; href=&#34;https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevD.76.013009&amp;amp;v=d0670bbf&#34;&gt;10.1103/PhysRevD.76.013009&lt;/a&gt; or other'
            )

    def test_with_jinja_escapes(self):
        """Test the tex2utf filter with jinja escapes."""
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['urlize'] = urlizer(
                ['arxiv_id', 'doi']
            )

            # TODO: urlize doesn't seem to return a Markup object?
            self.assertEqual(
                jenv.from_string(
                    '{{"something 10.1103/PhysRevD.76.013009 or other"|urlize}}'
                ).render(),
                'something &lt;a class=&#34;link-https&#34; data-doi=&#34;10.1103/PhysRevD.76.013009&#34; href=&#34;https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevD.76.013009&amp;amp;v=d0670bbf&#34;&gt;10.1103/PhysRevD.76.013009&lt;/a&gt; or other'
            )

            self.assertEqual(
                jenv.from_string(
                    '{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009"|urlize}}'
                ).render(),
                '&lt;script&gt;bad junk&lt;/script&gt; something &lt;a class=&#34;link-https&#34; data-doi=&#34;10.1103/PhysRevD.76.013009&#34; href=&#34;https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevD.76.013009&amp;amp;v=d0670bbf&#34;&gt;10.1103/PhysRevD.76.013009&lt;/a&gt;'
            )

    def test_doi_filter(self):
        """Test the urlizer DOI filter."""
        self.maxDiff = None
        with app.app_context():
            s = 'some test string 23$6#$5<>&456 http://google.com/notadoi'
            urlize_dois = urlizer(
                ['doi']
            )
            self.assertEqual(urlize_dois(s), str(escape(s)))

            doi = '10.1103/PhysRevD.76.013009'
            doiurl = urlize_dois(doi)
            self.assertRegex(doiurl, r'^<a', 'should start with a tag')
            self.assertEqual(
                doiurl,
                str(Markup('<a class="link-https" data-doi="10.1103/PhysRevD.76.013009" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevD.76.013009&amp;v=d0670bbf">10.1103/PhysRevD.76.013009</a>'))
            )

            s = f'something something {doi} endthing'
            doiurl = urlize_dois(s)
            self.assertRegex(
                doiurl, r'<a class="link-https" data-doi="', 'Have an A tag')
            self.assertRegex(doiurl, '^something something ')
            self.assertRegex(doiurl, ' endthing$')

            txt = '10.1103/PhysRevA.99.013009 10.1103/PhysRevZ.44.023009 10.1103/PhysRevX.90.012309 10.1103/BioRevX.44.123456'
            self.assertEqual(
                urlize_dois(txt),
                str(
                    Markup(
                        '<a class="link-https" data-doi="10.1103/PhysRevA.99.013009" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevA.99.013009&amp;v=94f8600c">10.1103/PhysRevA.99.013009</a> '
                        '<a class="link-https" data-doi="10.1103/PhysRevZ.44.023009" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevZ.44.023009&amp;v=bba1640c">10.1103/PhysRevZ.44.023009</a> '
                        '<a class="link-https" data-doi="10.1103/PhysRevX.90.012309" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevX.90.012309&amp;v=3a1daa37">10.1103/PhysRevX.90.012309</a> '
                        '<a class="link-https" data-doi="10.1103/BioRevX.44.123456" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FBioRevX.44.123456&amp;v=c8298ca6">10.1103/BioRevX.44.123456</a>'
                    )
                )
            )

            txt = '<script>Im from the user and Im bad</script>'
            self.assertEqual(
                urlize_dois(f'{doi} {txt}'),
                str(Markup(f'<a class="link-https" data-doi="10.1103/PhysRevD.76.013009" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevD.76.013009&amp;v=d0670bbf">10.1103/PhysRevD.76.013009</a> <script>Im from the user and Im bad</script>'))
            )

    def test_arxiv_id_urls_basic(self):
        """Test basic urlize for arXiv identifiers."""
        # a server name is needed for url_for to return something
        h = 'arxiv.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(urlize('', ['arxiv_id']), '')
            s = 'some text 134#%$$%&^^%*^&(()*_)_<>?:;[}}'
            self.assertEqual(urlize(s), str(escape(s)),
                             'filters should return escaped text')
            self.assertEqual(
                urlize('hep-th/9901001'),
                f'<a class="link-https" data-arxiv-id="hep-th/9901001" href="https://arxiv.org/abs/hep-th/9901001">hep-th/9901001</a>',
            )
            self.assertEqual(
                urlize('hep-th/9901001 hep-th/9901002'),
                f'<a class="link-https" data-arxiv-id="hep-th/9901001" href="https://arxiv.org/abs/hep-th/9901001">hep-th/9901001</a> <a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>'
            )

    def test_arxiv_id_urls_3(self):
        """Test more complex cases of urlize for arXiv identifiers."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(
                urlize('hep-th/9901002'),
                f'<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>',
            )
            self.assertEqual(
                urlize('hep-th/9901002\n'),
                f'<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>\n'
            )
            self.assertEqual(
                urlize('arXiv:dg-ga/9401001 hep-th/9901001 hep-th/9901002'),
                f'<a class="link-https" data-arxiv-id="dg-ga/9401001" href="https://arxiv.org/abs/dg-ga/9401001">arXiv:dg-ga/9401001</a> <a class="link-https" data-arxiv-id="hep-th/9901001" href="https://arxiv.org/abs/hep-th/9901001">hep-th/9901001</a> <a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>'
            )

    def test_arxiv_id_urls_punct(self):
        """Test cases of of urlize for arXiv identifiers with punctuation."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(
                urlize('hep-th/9901002.'),
                f'<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>.',
                'followed by period')
            self.assertEqual(
                urlize('0702.0003.'),
                f'<a class="link-https" data-arxiv-id="0702.0003" href="https://arxiv.org/abs/0702.0003">0702.0003</a>.',
                'followed by period')
            self.assertEqual(
                urlize('hep-th/9901001,hep-th/9901002'),
                f'<a class="link-https" data-arxiv-id="hep-th/9901001" href="https://arxiv.org/abs/hep-th/9901001">hep-th/9901001</a>,<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>',
                'filter_urls_ids_escape (ID linking) 3/7')
            self.assertEqual(
                urlize('0702.0003, something'),
                f'<a class="link-https" data-arxiv-id="0702.0003" href="https://arxiv.org/abs/0702.0003">0702.0003</a>, something',
                'followed by comma')
            self.assertEqual(
                urlize('(0702.0003) something'),
                f'(<a class="link-https" data-arxiv-id="0702.0003" href="https://arxiv.org/abs/0702.0003">0702.0003</a>) something',
                'in parens')

    def test_arxiv_id_urls_more(self):
        """Test urlize for arXiv identifiers that have mixed formatting."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(
                urlize('arXiv:dg-ga/9401001 hep-th/9901001 0704.0001'),
                f'<a class="link-https" data-arxiv-id="dg-ga/9401001" href="https://arxiv.org/abs/dg-ga/9401001">arXiv:dg-ga/9401001</a> <a class="link-https" data-arxiv-id="hep-th/9901001" href="https://arxiv.org/abs/hep-th/9901001">hep-th/9901001</a> <a class="link-https" data-arxiv-id="0704.0001" href="https://arxiv.org/abs/0704.0001">0704.0001</a>',
                'urlize (ID linking) 5/7')

    def test_arxiv_id_v(self):
        """Test urlize for arXiv identifers with version affix."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            self.assertEqual(
                urlize('arXiv:dg-ga/9401001v12 hep-th/9901001v2 0704.0001v1'),
                f'<a class="link-https" data-arxiv-id="dg-ga/9401001v12" href="https://arxiv.org/abs/dg-ga/9401001v12">arXiv:dg-ga/9401001v12</a> <a class="link-https" data-arxiv-id="hep-th/9901001v2" href="https://arxiv.org/abs/hep-th/9901001v2">hep-th/9901001v2</a> <a class="link-https" data-arxiv-id="0704.0001v1" href="https://arxiv.org/abs/0704.0001v1">0704.0001v1</a>',
                'arxiv ids with version numbers')

    @unittest.skip("TODO: confirm actual desired behavior")
    def test_vixra(self):
        """Test urlize for identifiers prefixed by viXra."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h

        with app.app_context():
            self.assertEqual(urlize('viXra:0704.0001 viXra:1003.0123'),
                             'viXra:0704.0001 viXra:1003.0123')

            # this is what was expected in legacy, but it doesn't seem right:
            # self.assertEqual(
            #     urlize('vixra:0704.0001'),
            #     f'vixra:<a href="https://arxiv.org/abs/0704.0001">0704.0001</a>')

    def test_arxiv_id_urls_escaping(self):
        """Test proper escaping when urlize applied."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            ax_id = 'hep-th/9901002'

            user_entered_txt = ' <div>div should be escaped</div>'
            ex_txt = Markup(user_entered_txt)
            self.assertEqual(
                urlize(ax_id + user_entered_txt),
                f'<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>{ex_txt}',
                'Dealing with user entered text with html that should be escaped for safety'
            )

            jinja_escaped_txt = Markup(
                ' <div>div should already be escaped by jinja2</div>')
            self.assertEqual(
                urlize(ax_id + jinja_escaped_txt),
                f'<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a>{jinja_escaped_txt}',
                'Dealing with text that has been escaped by Jinja2 already')

    def test_arxiv_id_jinja_escapes(self):
        self.maxDiff = None
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():

            jenv = Environment(autoescape=True)
            jenv.filters['urlize'] = jenv.filters['urlize'] = urlizer(
                ['arxiv_id', 'doi', 'url']
            )

            self.assertEqual(
                jenv.from_string(
                    '{{"something hep-th/9901002 or other"|urlize|safe}}').
                render(),
                f'something <a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a> or other'
            )

            self.assertEqual(
                jenv.from_string(
                    '{{"<script>bad junk</script> something 10.1103/PhysRevD.76.013009"|urlize|safe}}'
                ).render(),
                '<script>bad junk</script> something <a class="link-https" data-doi="10.1103/PhysRevD.76.013009" href="https://arxiv.org/ct?url=https%3A%2F%2Fdx.doi.org%2F10.1103%2FPhysRevD.76.013009&amp;v=d0670bbf">10.1103/PhysRevD.76.013009</a>'
            )

            self.assertEqual(
                jenv.from_string(
                    '{{"<script>bad junk</script> http://google.com bla bla '
                    'hep-th/9901002 bla"|urlize|safe}}').
                render(),
                '<script>bad junk</script> '
                '<a class="link-external link-http" href="http://google.com" rel="external">this http URL</a> bla bla '
                f'<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a> bla',
                'should not double escape')

    def test_line_break(self):
        """Test the abstract lf to br tag filter."""
        self.assertEqual(abstract_lf_to_br('blal\n  bla'), 'blal\n<br />bla')

        self.assertEqual(abstract_lf_to_br(
            '\nblal\n  bla'), '\nblal\n<br />bla')

        self.assertEqual(abstract_lf_to_br('\n blal\n  bla'),
                         '\n blal\n<br />bla',
                         'need to not do <br /> on first line')
        self.assertEqual(abstract_lf_to_br('blal\n\nbla'), 'blal\nbla',
                         'skip blank lines')

    def test_line_break_jinja(self):
        """Test the abstract lf to br tag filter with urlize on arXiv IDs."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['urlize'] = urlize
            jenv.filters['line_break'] = abstract_lf_to_br

            self.assertEqual(
                jenv.from_string(
                    '{{"<script>bad junk</script> http://google.com something or \n'
                    '\n'
                    'no double \\n'
                    ' should have br\n'
                    'hep-th/9901002 other"|line_break|urlize|safe}}'
                ).render(),
                '&lt;script&gt;bad junk&lt;/script&gt; '
                '<a class="link-external link-http" href="http://google.com" rel="external">this http URL</a>'
                ' something or \n'
                'no double \n'
                '<br>should have br\n'
                '<a class="link-https" data-arxiv-id="hep-th/9901002" href="https://arxiv.org/abs/hep-th/9901002">hep-th/9901002</a> other',
                'line_break and arxiv_id_urls should work together'
            )

    def test_tex2utf(self):
        """Test the tex2utf filter."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['urlize'] = urlize
            jenv.filters['line_break'] = abstract_lf_to_br
            jenv.filters['tex2utf'] = f_tex2utf

            self.assertEqual(
                jenv.from_string('{{""|tex2utf|urlize|safe}}').render(),
                ''
            )

            title = jenv.from_string(
                '{{"Finite-Size and Finite-Temperature Effects in the Conformally Invariant O(N) Vector Model for 2<d<4"|tex2utf|urlize|safe}}'
            ).render()
            self.assertEqual(
                title,
                'Finite-Size and Finite-Temperature Effects in the Conformally Invariant O(N) Vector Model for 2&lt;d&lt;4',
                'tex2utf and arxiv_id_urls should handle < and > ARXIVNG-1227'
            )

            self.assertEqual(f_tex2utf('Lu\\\'i'), 'Luí')
            self.assertEqual(f_tex2utf(Markup('Lu\\\'i')), 'Luí')
            self.assertEqual(f_tex2utf(Markup(escape('Lu\\\'i'))), 'Luí')

    def test_entity_to_utf(self):
        """Test the entity to utf filter."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['entity_to_utf'] = entity_to_utf
            self.assertEqual(
                jenv.from_string('{{ "Mart&#xED;n"|entity_to_utf }}').render(),
                'Martín', 'entity_to_utf should work')
            self.assertEqual(
                jenv.from_string(
                    '{{ "<Mart&#xED;n>"|entity_to_utf }}').render(),
                '&lt;Martín&gt;',
                'entity_to_utf should work even with < or >')

    def test_arxiv_urlize_no_email_links(self):
        """Test to ensure email addresses are not turned into links."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            jenv = Environment(autoescape=True)
            jenv.filters['urlize'] = urlize

            self.assertEqual(
                jenv.from_string(
                    '{{ "bob@example.com"|urlize|safe }}').render(),
                'bob@example.com',
                'arxiv_urlize should not turn emails into links')
            self.assertEqual(
                jenv.from_string(
                    '{{ "<bob@example.com>"|urlize|safe }}').render(),
                '&lt;bob@example.com&gt;',
                'arxiv_urlize should work even with < or >')

    def test_arxiv_urlize(self):
        """Multiple basic urlize tests."""
        h = 'sosmooth.org'
        app.config['SERVER_NAME'] = h
        with app.app_context():
            self.assertEqual(
                urlize('http://example.com/'),
                '<a class="link-external link-http" href="http://example.com/" rel="external">this http URL</a>',
                'urlize (URL linking) 1/6')
            self.assertEqual(
                urlize('https://example.com/'),
                '<a class="link-external link-https" href="https://example.com/" rel="external">this https URL</a>',
                'urlize (URL linking) 2/6')
            self.assertEqual(
                urlize('ftp://example.com/'),
                '<a class="link-external link-ftp" href="ftp://example.com/" rel="external">this ftp URL</a>',
                'urlize (URL linking) 3/6')
            self.assertEqual(
                urlize('http://example.com/.hep-th/9901001'),
                '<a class="link-external link-http" href="http://example.com/.hep-th/9901001" rel="external">this http URL</a>',
                'urlize (URL linking) 4/6')
            self.assertEqual(
                urlize(
                    'http://projecteuclid.org/euclid.bj/1151525136'
                ),
                '<a class="link-external link-http" href="http://projecteuclid.org/euclid.bj/1151525136" rel="external">this http URL</a>',
                'urlize (URL linking) 6/6')
            self.assertEqual(
                urlize(
                    '  Correction to Bernoulli (2006), 12, 551--570 http://projecteuclid.org/euclid.bj/1151525136'),
                Markup('  Correction to Bernoulli (2006), 12, 551--570 <a class="link-external link-http" href="http://projecteuclid.org/euclid.bj/1151525136" rel="external">this http URL</a>'),
                'urlize (URL linking) 6/6')
            # shouldn't match
            self.assertEqual(
                urlize('2448446.4710(5)'), '2448446.4710(5)',
                'urlize (should not match) 1/9')
            self.assertEqual(
                urlize('HJD=2450274.4156+/-0.0009'),
                'HJD=2450274.4156+/-0.0009',
                'urlize (should not match) 2/9')
            self.assertEqual(
                urlize('T_min[HJD]=49238.83662(14)+0.146352739(11)E.'),
                'T_min[HJD]=49238.83662(14)+0.146352739(11)E.',
                'urlize (should not match) 3/9')
            self.assertEqual(
                urlize('Pspin=1008.3408s'), 'Pspin=1008.3408s',
                'urlize (should not match) 4/9')
            self.assertEqual(
                urlize('2453527.87455^{+0.00085}_{-0.00091}'),
                '2453527.87455^{+0.00085}_{-0.00091}',
                'urlize (should not match) 5/9')
            self.assertEqual(
                urlize('2451435.4353'), '2451435.4353',
                'urlize (should not match) 6/9')
            self.assertEqual(
                urlize('cond-mat/97063007'),
                '<a class="link-https" data-arxiv-id="cond-mat/9706300" href="https://arxiv.org/abs/cond-mat/9706300">cond-mat/9706300</a>7',
                'urlize (should match) 7/9')

            self.assertEqual(
                urlize('[http://onion.com/something-funny-about-arxiv-1234]'),
                '[<a class="link-external link-http" href="http://onion.com/something-funny-about-arxiv-1234" rel="external">this http URL</a>]')

            self.assertEqual(
                urlize('[http://onion.com/?q=something-funny-about-arxiv.1234]'),
                '[<a class="link-external link-http" href="http://onion.com/?q=something-funny-about-arxiv.1234" rel="external">this http URL</a>]')

            self.assertEqual(
                urlize('http://onion.com/?q=something funny'),
                '<a class="link-external link-http" href="http://onion.com/?q=something" rel="external">this http URL</a> funny',
                'Spaces CANNOT be expected to be part of URLs')

            self.assertEqual(
                urlize('"http://onion.com/something-funny-about-arxiv-1234"'),
                '"<a class="link-external link-http" href="http://onion.com/something-funny-about-arxiv-1234" rel="external">this http URL</a>"',
                'Should handle URL surrounded by double quotes')
