"""Tests for author and affiliation parsing."""
from unittest import TestCase

from browse.services.document.author_affil import parse_author_affil, _split_authors


class TestAuthorAffiliationParsing(TestCase):

    def test_split_authors(self):
        self.assertListEqual(_split_authors('Simeon Warner'),
                             ['Simeon Warner'])

        self.assertListEqual(_split_authors('The DELPHI Collaboration, J. Abdallah, et al'),
                             ['The DELPHI Collaboration', ',', 'J. Abdallah', ',', 'et al'])

        self.assertListEqual(_split_authors('BELLE Collaboration: A Person, Nother Person'),
                             ['BELLE Collaboration', ':', 'A Person', ',', 'Nother Person'])

        self.assertListEqual(_split_authors('Simeon Warner, Herbert Van de Sompel'),
                             ['Simeon Warner', ',', 'Herbert Van de Sompel'])

        self.assertListEqual(
            _split_authors('An Author'),
            ['An Author'],
            'single author'
        )

        self.assertListEqual(
            _split_authors(''),
            [],
            'empty author'
        )

        self.assertListEqual(
            _split_authors('An Author (affil)'),
            ['An Author', '(affil)'],
            'single author with affil'
        )
        self.assertListEqual(
            _split_authors('An Author     (affil)'),
            ['An Author', '(affil)'],
            'single author with affil'
        )
        self.assertListEqual(
            _split_authors('An Author and Another P. H. J. Author (affil)'),
            ['An Author', ',', 'Another P. H. J. Author', '(affil)'],
            'double author with affil'
        )
        self.assertListEqual(
            _split_authors(
                'John Von Neumann, Herbert Van de Sompel, Fred Bloggs, Jr, et al'),
            ['John Von Neumann', ',', 'Herbert Van de Sompel',
             ',', 'Fred Bloggs, Jr', ',', 'et al'],
            'multiple with prefixes and suffixes'
        )
        self.assertListEqual(
            _split_authors('sum won ( whatever affil  data   unmunged  )'),
            ['sum won', '( whatever affil data unmunged )'],
            'one author, two labs'
        )
        self.assertListEqual(
            _split_authors('sum won(1,2)((1)lab a,(2)lab b)'),
            ['sum won', '(1,2)', '((1)lab a,(2)lab b)'],
            'one author, two labs'
        )

    def test_parse_author_affil_basic(self):
        self.assertListEqual(parse_author_affil(
            'Simeon Warner'), [['Warner', 'Simeon', '']])

        self.assertListEqual(
            parse_author_affil('Simeon Warner Jr'),
            [['Warner', 'Simeon', 'Jr']])

        self.assertListEqual(
            parse_author_affil('Simeon Warner Jr.'),
            [['Warner', 'Simeon', 'Jr.']])

        self.assertListEqual(
            parse_author_affil('Simeon Warner Sr'),
            [['Warner', 'Simeon', 'Sr']])

        self.assertListEqual(
            parse_author_affil('Simeon Warner Sr.'),
            [['Warner', 'Simeon', 'Sr.']])

        self.assertListEqual(
            parse_author_affil('SM Warner'),
            [['Warner', 'SM', '']])

        self.assertListEqual(
            parse_author_affil('SM. Warner'),
            [['Warner', 'SM.', '']])

    def test_parse_author_affil_basic2(self):
        self.assertListEqual(
            parse_author_affil('S.M. Warner'),
            [['Warner', 'S. M.', '']])

        self.assertListEqual(
            parse_author_affil('John Von Neumann'),
            [['Von Neumann', 'John', '']])

        self.assertListEqual(
            parse_author_affil('Herbert Van de Sompel'),
            [['Van de Sompel', 'Herbert', '']])

        self.assertListEqual(
            parse_author_affil('del Norte'),
            [['Norte', 'del', '']])

        self.assertListEqual(
            parse_author_affil('Fred del Norte'),
            [['del Norte', 'Fred', '']])

        self.assertListEqual(
            parse_author_affil('BELLE'),
            [['BELLE', '', '']])

        self.assertListEqual(
            parse_author_affil('BELLE Collaboration: A Person, Nother Person'),
            [
                ['BELLE Collaboration', '', ''],
                ['Person', 'A', ''],
                ['Person', 'Nother', '']
            ])

        self.assertListEqual(parse_author_affil('The DELPHI Collaboration, J. Abdallah, et al'),
                             [['The DELPHI Collaboration', '', ''], ['Abdallah', 'J.', '']])

        self.assertListEqual(parse_author_affil('Ali Vaziri Astaneh, Federico Fuentes'),
                             [['Vaziri Astaneh', 'Ali', ''],['Fuentes', 'Federico', '']])

    def test_parse_author_affil_with_affiliations(self):
        self.assertListEqual(
            parse_author_affil('sum won (lab a)'),
            [['won', 'sum', '', 'lab a']])

        self.assertListEqual(
            parse_author_affil('sum won (lab a; lab b)'),
            [['won', 'sum', '', 'lab a; lab b']])

        self.assertListEqual(
            parse_author_affil('sum won (lab a, lab b)'),
            [['won', 'sum', '', 'lab a, lab b']])

        self.assertListEqual(
            parse_author_affil('sum won (1,2) ( (1) lab a, (2) lab b)'),
            [['won', 'sum', '', 'lab a', 'lab b']])

        self.assertListEqual(
            parse_author_affil('sum won(1,2)((1)lab a,(2)lab b)'),
            [['won', 'sum', '', 'lab a', 'lab b']])

        self.assertListEqual(
            parse_author_affil('a.b.first, c.d.second (affil)'),
            [['first', 'a. b.', '', 'affil'], ['second', 'c. d.', '', 'affil']])

        self.assertListEqual(
            parse_author_affil('a.b.first (affil), c.d.second (affil)'),
            [['first', 'a. b.', '', 'affil'], ['second', 'c. d.', '', 'affil']])

        self.assertListEqual(
            parse_author_affil(
                'a.b.first, c.d.second (1), e.f.third, g.h.forth (2,3) ((1) affil1, (2) affil2, (3) affil3)'
            ),
            [
                ['first', 'a. b.', '', 'affil1'],
                ['second', 'c. d.', '', 'affil1'],
                ['third', 'e. f.', '', 'affil2', 'affil3'],
                ['forth', 'g. h.', '', 'affil2', 'affil3']
            ])

        self.assertListEqual(
            parse_author_affil((
                "QUaD collaboration: S. Gupta (1), P. Ade (1), J. Bock (2,3), M. Bowden "
                "(1,4), M. L. Brown (5), G. Cahill (6), P. G. Castro (7,8), S. Church (4), T. "
                "Culverhouse (9), R. B. Friedman (9), K. Ganga (10), W. K. Gear (1), J. "
                "Hinderks (5,11), J. Kovac (3), A. E. Lange (4), E. Leitch (2,3), S. J. "
                "Melhuish (12), Y. Memari (7), J. A. Murphy (6), A. Orlando (1,3), C. "
                "O'Sullivan (6), L. Piccirillo (12), C. Pryke (9), N. Rajguru (1,13), B. "
                "Rusholme (4,14), R. Schwarz (9), A. N. Taylor (7), K. L. Thompson (4), A. H. "
                "Turner (1), E. Y. S. Wu (4), M. Zemcov (1,2,3) ((1) Cardiff University, (2) "
                "JPL, (3) Caltech, (4) Stanford University, (5) University of Cambridge, (6) "
                "National University of Ireland Maynooth, (7) University of Edinburgh, (8) "
                "Universidade Tecnica de Lisboa, (9) University of Chicago, (10) Laboratoire "
                "APC/CNRS, (11) NASA Goddard, (12) University of Manchester, (13) UCL, (14) "
                "IPAC) "
            )),
            [
                ["QUaD collaboration", "", ""],
                ["Gupta", "S.", "", "Cardiff University"],
                ["Ade", "P.", "", "Cardiff University"],
                ["Bock", "J.", "", "JPL", "Caltech"],
                ["Bowden", "M.", "", "Cardiff University", "Stanford University"],
                ["Brown", "M. L.", "", "University of Cambridge"],
                ["Cahill", "G.", "", "National University of Ireland Maynooth"],
                [
                    "Castro", "P. G.", "",
                    "University of Edinburgh",
                    "Universidade Tecnica de Lisboa"
                ],
                ["Church", "S.", "", "Stanford University"],
                ["Culverhouse", "T.", "", "University of Chicago"],
                ["Friedman", "R. B.", "", "University of Chicago"],
                ["Ganga", "K.", "", "Laboratoire APC/CNRS"],
                ["Gear", "W. K.", "", "Cardiff University"],
                ["Hinderks", "J.", "", "University of Cambridge", "NASA Goddard"],
                ["Kovac", "J.", "", "Caltech"],
                ["Lange", "A. E.", "", "Stanford University"],
                ["Leitch", "E.", "", "JPL", "Caltech"],
                ["Melhuish", "S. J.", "", "University of Manchester"],
                ["Memari", "Y.", "", "University of Edinburgh"],
                ["Murphy", "J. A.", "", "National University of Ireland Maynooth"],
                ["Orlando", "A.", "", "Cardiff University", "Caltech"],
                ["O'Sullivan", "C.", "", "National University of Ireland Maynooth"],
                ["Piccirillo", "L.", "", "University of Manchester"],
                ["Pryke", "C.", "", "University of Chicago"],
                ["Rajguru", "N.", "", "Cardiff University", "UCL"],
                ["Rusholme", "B.", "", "Stanford University", "IPAC"],
                ["Schwarz", "R.", "", "University of Chicago"],
                ["Taylor", "A. N.", "", "University of Edinburgh"],
                ["Thompson", "K. L.", "", "Stanford University"],
                ["Turner", "A. H.", "", "Cardiff University"],
                ["Wu", "E. Y. S.", "", "Stanford University"],
                ["Zemcov", "M.", "", "Cardiff University", "JPL", "Caltech"]
            ],
            'parse_author_affil (mind-blowing) 1/1'
        )

        # Problem case with 1110.4366
        self.assertListEqual(
            parse_author_affil(
                'Matthew Everitt, Robert M. Heath and Viv Kendon'),
            [['Everitt', 'Matthew', ''],
             ['Heath', 'Robert M.', ''],
             ['Kendon', 'Viv', '']],
            'parse_author_affil for 1110.4366'
        )

        # look like bugs, but aren't
        self.assertListEqual(
            parse_author_affil('sum won ((lab a), (lab b))'),
            [['won', 'sum', '']],
            'parse_author_affil (bug imposter) 1/2'
        )
        self.assertListEqual(
            parse_author_affil('sum won ((lab a) (lab b))'),
            [['won', 'sum', '']],
            'parse_author_affil (bug imposter) 2/2'
        )

        self.assertListEqual(
            parse_author_affil('Anatoly Zlotnik and Jr-Shin Li'),
            [['Zlotnik', 'Anatoly', ''],
             ['Li', 'Jr-Shin', '']],
            'jr issue (Anatoly Zlotnik and Jr-Shin Li)'
        )

        # ====== Extra tests for arXiv::AuthorAffil ARXIVDEV-728 ======

        # [parse_author_affil]
        self.assertListEqual(
            parse_author_affil(''),
            [],
            'parse_author_affil (empty)'
        )
        self.assertListEqual(
            parse_author_affil('Simeon Warner Jr'),
            [['Warner', 'Simeon', 'Jr']],
            'parse_author_affil (basic) 2/12'
        )
        self.assertListEqual(
            parse_author_affil('BELLE Collaboration'),
            [['BELLE Collaboration', '', '']],
            'parse_author_affil (lone "BELLE Collaboration") 2/3'
        )

        self.assertListEqual(
            parse_author_affil('BELLE Collaboration'),
            [['BELLE Collaboration', '', '']],
            'parse_author_affil (lone "BELLE Collaboration") 2/3'
        )
