"""Tests for author and affiliation parsing."""
from unittest import TestCase

from browse.domain.author_affil import parse_author_affil, split_authors


class TestAuthorAffiliationParsing(TestCase):

    def test_split_authors(self):
        self.assertListEqual(split_authors('Simeon Warner'),
                             ['Simeon Warner'])

        self.assertListEqual(split_authors('BELLE Collaboration: A Person, Nother Person'),
                             ['BELLE Collaboration', ':', 'A Person', ',', 'Nother Person'])

        self.assertListEqual(split_authors('Simeon Warner, Herbert Van de Sompel'),
                             ['Simeon Warner', ',', 'Herbert Van de Sompel'])

        self.assertListEqual(split_authors(
            'a.b.first, c.d.second (1), e.f.third, g.h.forth (2,3) ((1) affil1, (2) affil2, (3) affil3)'),
            ['a.b.first',
             ',',
             'c.d.second',
             '(1)',
             ',',
             'e.f.third',
             ',',
             'g.h.forth',
             '(2,3)',
             '((1)',
             'affil1',
             ',',
             '(2)',
             'affil2',
             ',',
             '(3)',
             'affil3)']
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

#
# # [parse_author_affil_utf]
# is_deeply(
#     parse_author_affil_utf('Simeon Warner'),
#     [ [ 'Warner', 'Simeon', '' ] ],
#     'parse_author_affil_utf (basic) 1/12'
# );
# is_deeply(
#     parse_author_affil_utf('Simeon Warner Jr'),
#     [ [ 'Warner', 'Simeon', 'Jr' ] ],
#     'parse_author_affil_utf (basic) 2/12'
# );
# is_deeply(
#     parse_author_affil_utf('Simeon Warner Jr.'),
#     [ [ 'Warner', 'Simeon', 'Jr.' ] ],
#     'parse_author_affil_utf (basic) 3/12'
# );
# is_deeply(
#     parse_author_affil_utf('Simeon Warner Sr'),
#     [ [ 'Warner', 'Simeon', 'Sr' ] ],
#     'parse_author_affil_utf (basic) 4/12'
# );
# is_deeply(
#     parse_author_affil_utf('Simeon Warner Sr.'),
#     [ [ 'Warner', 'Simeon', 'Sr.' ] ],
#     'parse_author_affil_utf (basic) 5/12'
# );
#
# is_deeply(
#     parse_author_affil_utf('SM Warner'),
#     [ [ 'Warner', 'SM', '' ] ],
#     'parse_author_affil_utf (basic) 6/12'
# );
# is_deeply(
#     parse_author_affil_utf('SM. Warner'),
#     [ [ 'Warner', 'SM.', '' ] ],
#     'parse_author_affil_utf (basic) 7/12'
# );
# is_deeply(
#     parse_author_affil_utf('S.M. Warner'),
#     [ [ 'Warner', 'S. M.', '' ] ],
#     'parse_author_affil_utf (basic) 8/12'
# );
#
# is_deeply(
#     parse_author_affil_utf('John Von Neumann'),
#     [ [ 'Von Neumann', 'John', '' ] ],
#     'parse_author_affil_utf (basic) 9/12'
# );
# is_deeply(
#     parse_author_affil_utf('Herbert Van de Sompel'),
#     [ [ 'Van de Sompel', 'Herbert', '' ] ],
#     'parse_author_affil_utf (basic) 10/12'
# );
#
# is_deeply(
#     parse_author_affil_utf('del Norte'),
#     [ [ 'Norte', 'del', '' ] ],
#     'parse_author_affil_utf (basic) 11/12'
# );
# is_deeply(
#     parse_author_affil_utf('Fred del Norte'),
#     [ [ 'del Norte', 'Fred', '' ] ],
#     'parse_author_affil_utf (basic) 12/12'
# );
#
# is_deeply(
#     parse_author_affil_utf('BELLE'),
#     [ [ 'BELLE', '', '' ] ],
#     'parse_author_affil_utf (intermediate) 1/3'
# );
# is_deeply(
#     parse_author_affil_utf('BELLE Collaboration: A Person, Nother Person'),
#     [
#         [ 'BELLE Collaboration', '',       '' ],
#         [ 'Person',              'A',      '' ],
#         [ 'Person',              'Nother', '' ]
#     ],
#     'parse_author_affil_utf (intermediate) 3/3'
# );
#
# is_deeply(
#     parse_author_affil_utf('sum won (lab a)'),
#     [ [ 'won', 'sum', '', 'lab a' ] ],
#     'parse_author_affil_utf (advanced) 1/8'
# );
# is_deeply(
#     parse_author_affil_utf('sum won (lab a; lab b)'),
#     [ [ 'won', 'sum', '', 'lab a; lab b' ] ],
#     'parse_author_affil_utf (advanced) 2/8'
# );
# is_deeply(
#     parse_author_affil_utf('sum won (lab a, lab b)'),
#     [ [ 'won', 'sum', '', 'lab a, lab b' ] ],
#     'parse_author_affil_utf (advanced) 3/8'
# );
# is_deeply(
#     parse_author_affil_utf('sum won (1,2) ( (1) lab a, (2) lab b)'),
#     [ [ 'won', 'sum', '', 'lab a', 'lab b' ] ],
#     'parse_author_affil_utf (advanced) 4/8'
# );
# is_deeply(
#     parse_author_affil_utf('sum won(1,2)((1)lab a,(2)lab b)'),
#     [ [ 'won', 'sum', '', 'lab a', 'lab b' ] ],
#     'parse_author_affil_utf (advanced) 5/8'
# );
#
# is_deeply(
#     parse_author_affil_utf('a.b.first, c.d.second (affil)'),
#     [ [ 'first', 'a. b.', '', 'affil' ], [ 'second', 'c. d.', '', 'affil' ] ],
#     'parse_author_affil_utf (advanced) 6/8'
# );
# is_deeply(
#     parse_author_affil_utf('a.b.first (affil), c.d.second (affil)'),
#     [ [ 'first', 'a. b.', '', 'affil' ], [ 'second', 'c. d.', '', 'affil' ] ],
#     'parse_author_affil_utf (advanced) 7/8'
# );
# is_deeply(
#     parse_author_affil_utf(
# 'a.b.first, c.d.second (1), e.f.third, g.h.forth (2,3) ((1) affil1, (2) affil2, (3) affil3)'
#     ),
#     [
#         [ 'first',  'a. b.', '', 'affil1' ],
#         [ 'second', 'c. d.', '', 'affil1' ],
#         [ 'third', 'e. f.', '', 'affil2', 'affil3' ],
#         [ 'forth', 'g. h.', '', 'affil2', 'affil3' ]
#     ],
#     'parse_author_affil_utf (advanced) 8/8'
# );
#
# is_deeply(
#     parse_author_affil_utf(
#         "QUaD collaboration: S. Gupta (1), P. Ade (1), J. Bock (2,3), M. Bowden
#   (1,4), M. L. Brown (5), G. Cahill (6), P. G. Castro (7,8), S. Church (4), T.
#   Culverhouse (9), R. B. Friedman (9), K. Ganga (10), W. K. Gear (1), J.
#   Hinderks (5,11), J. Kovac (3), A. E. Lange (4), E. Leitch (2,3), S. J.
#   Melhuish (12), Y. Memari (7), J. A. Murphy (6), A. Orlando (1,3), C.
#   O'Sullivan (6), L. Piccirillo (12), C. Pryke (9), N. Rajguru (1,13), B.
#   Rusholme (4,14), R. Schwarz (9), A. N. Taylor (7), K. L. Thompson (4), A. H.
#   Turner (1), E. Y. S. Wu (4), M. Zemcov (1,2,3) ((1) Cardiff University, (2)
#   JPL, (3) Caltech, (4) Stanford University, (5) University of Cambridge, (6)
#   National University of Ireland Maynooth, (7) University of Edinburgh, (8)
#   Universidade Tecnica de Lisboa, (9) University of Chicago, (10) Laboratoire
#   APC/CNRS, (11) NASA Goddard, (12) University of Manchester, (13) UCL, (14)
#   IPAC)"
#     ),
#     [
#         [ "QUaD collaboration", "", "" ],
#         [ "Gupta", "S.", "", "Cardiff University" ],
#         [ "Ade",   "P.", "", "Cardiff University" ],
#         [ "Bock",   "J.", "", "JPL",                "Caltech" ],
#         [ "Bowden", "M.", "", "Cardiff University", "Stanford University" ],
#         [ "Brown",  "M. L.", "", "University of Cambridge" ],
#         [ "Cahill", "G.",    "", "National University of Ireland Maynooth" ],
#         [
#             "Castro", "P. G.", "",
#             "University of Edinburgh",
#             "Universidade Tecnica de Lisboa"
#         ],
#         [ "Church",      "S.",    "", "Stanford University" ],
#         [ "Culverhouse", "T.",    "", "University of Chicago" ],
#         [ "Friedman",    "R. B.", "", "University of Chicago" ],
#         [ "Ganga",       "K.",    "", "Laboratoire APC/CNRS" ],
#         [ "Gear",        "W. K.", "", "Cardiff University" ],
#         [ "Hinderks", "J.",    "", "University of Cambridge", "NASA Goddard" ],
#         [ "Kovac",    "J.",    "", "Caltech" ],
#         [ "Lange",    "A. E.", "", "Stanford University" ],
#         [ "Leitch",   "E.",    "", "JPL",                     "Caltech" ],
#         [ "Melhuish", "S. J.", "", "University of Manchester" ],
#         [ "Memari",   "Y.",    "", "University of Edinburgh" ],
#         [ "Murphy",   "J. A.", "", "National University of Ireland Maynooth" ],
#         [ "Orlando", "A.", "", "Cardiff University", "Caltech" ],
#         [ "O'Sullivan", "C.", "", "National University of Ireland Maynooth" ],
#         [ "Piccirillo", "L.", "", "University of Manchester" ],
#         [ "Pryke",      "C.", "", "University of Chicago" ],
#         [ "Rajguru",  "N.",       "", "Cardiff University",  "UCL" ],
#         [ "Rusholme", "B.",       "", "Stanford University", "IPAC" ],
#         [ "Schwarz",  "R.",       "", "University of Chicago" ],
#         [ "Taylor",   "A. N.",    "", "University of Edinburgh" ],
#         [ "Thompson", "K. L.",    "", "Stanford University" ],
#         [ "Turner",   "A. H.",    "", "Cardiff University" ],
#         [ "Wu",       "E. Y. S.", "", "Stanford University" ],
#         [ "Zemcov", "M.", "", "Cardiff University", "JPL", "Caltech" ]
#     ],
#     'parse_author_affil_utf (mind-blowing) 1/1'
# );
#
# # Problem case with 1110.4366
# is_deeply(
#     parse_author_affil_utf('Matthew Everitt, Robert M. Heath and Viv Kendon'),
#     [ [ 'Everitt', 'Matthew', '' ],
#       [ 'Heath', 'Robert M.', '' ],
#       [ 'Kendon', 'Viv', '' ] ],
#     'parse_author_affil_utf for 1110.4366'
# );
#
# # look like bugs, but aren't
# is_deeply(
#     parse_author_affil_utf('sum won ((lab a), (lab b))'),
#     [ [ 'won', 'sum', '' ] ],
#     'parse_author_affil_utf (bug imposter) 1/2'
# );
# is_deeply(
#     parse_author_affil_utf('sum won ((lab a) (lab b))'),
#     [ [ 'won', 'sum', '' ] ],
#     'parse_author_affil_utf (bug imposter) 2/2'
# );
#
# is_deeply(
#     parse_author_affil_utf('Anatoly Zlotnik and Jr-Shin Li'),
#     [ [ 'Zlotnik', 'Anatoly', '' ],
#       [ 'Li', 'Jr-Shin', ''] ],
#     'jr issue (Anatoly Zlotnik and Jr-Shin Li)'
# );
#
# # ====== Extra tests for arXiv::AuthorAffil ARXIVDEV-728 ======
#
# # [parse_author_affil]
# is_deeply(
#     parse_author_affil(''),
#     [],
#     'parse_author_affil (empty)'
# );
# is_deeply(
#     parse_author_affil('Simeon Warner Jr'),
#     [ [ 'Warner', 'Simeon', 'Jr' ] ],
#     'parse_author_affil (basic) 2/12'
# );
# is_deeply(
#     parse_author_affil('BELLE Collaboration'),
#     [ [ 'BELLE Collaboration', '', '' ] ],
#     'parse_author_affil (lone "BELLE Collaboration") 2/3'
# );
#
# is_deeply(
#     parse_author_affil_utf('BELLE Collaboration'),
#     [ [ 'BELLE Collaboration', '', '' ] ],
#     'parse_author_affil_utf (lone "BELLE Collaboration") 2/3'
# );
#
# ################## split_authors ####################
#
# is_deeply(
#     split_authors(''),
#     [],
#     'empty author'
# );
# is_deeply(
#     split_authors('An Author'),
#     [ 'An Author' ],
#     'single author'
# );
# is_deeply(
#     split_authors('An Author (affil)'),
#     [ 'An Author', '(affil)' ],
#     'single author with affil'
# );
# is_deeply(
#     split_authors('An Author     (affil)'),
#     [ 'An Author', '(affil)' ],
#     'single author with affil'
# );
# is_deeply(
#     split_authors('An Author and Another P. H. J. Author (affil)'),
#     [ 'An Author', ',', 'Another P. H. J. Author', '(affil)' ],
#     'double author with affil'
# );
# is_deeply(
#     split_authors('John Von Neumann, Herbert Van de Sompel, Fred Bloggs, Jr, et al'),
#     [ 'John Von Neumann', ',', 'Herbert Van de Sompel', ',', 'Fred Bloggs, Jr', ',', 'et al' ],
#     'multiple with prefixes and suffixes'
# );
# is_deeply(
#     split_authors('sum won ( whatever affil  data   unmunged  )'),
#     [ 'sum won','( whatever affil data unmunged )' ],
#     'one author, two labs'
# );
# is_deeply(
#     split_authors('sum won(1,2)((1)lab a,(2)lab b)'),
#     [ 'sum won','(1,2)','((1)lab a,(2)lab b)' ],
#     'one author, two labs'
# );
