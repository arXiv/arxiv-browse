"""Tests for search service author link creation. """

from unittest import TestCase

from browse.domain import metadata
from browse.services.document.metadata import AbsMetaSession
from browse.services.search.search_authors import queries_for_authors, split_long_author_list


class TestAuthorLinkCreation(TestCase):
    def test_basic(self):
        out = queries_for_authors('')
        self.assertIsInstance(out, list)
        self.assertListEqual(out, [])

        out = queries_for_authors('Fred')
        self.assertIsInstance(out, list)
        self.assertListEqual(out, [('Fred', 'Fred')])

        out = queries_for_authors('J. R. Webb')
        self.assertIsInstance(out, list)
        self.assertListEqual(out, [('J. R. Webb', 'Webb, J R')])

        out = queries_for_authors('J. R. Webb, Fred')
        self.assertIsInstance(out, list)
        self.assertListEqual(
            out, [('J. R. Webb', 'Webb, J R'), ', ', ('Fred', 'Fred')])

        out = queries_for_authors("Fred Blogs (a), Jim Smith (b) (c)")
        self.assertListEqual(out, [('Fred Blogs', 'Blogs, F'),
                                   '(a)', ', ', ('Jim Smith', 'Smith, J'),
                                   '(b)', '(c)'])

        out = queries_for_authors("Francesca von Braun-Bates")
        self.assertListEqual(
            out, [("Francesca von Braun-Bates", 'von Braun-Bates, F')])

        out = queries_for_authors("Fritz Moritz von Rohrscheidt")
        self.assertListEqual(
            out, [("Fritz Moritz von Rohrscheidt", "von Rohrscheidt, F M")])

        out = queries_for_authors("C. de la Fuente Marcos")
        self.assertListEqual(
            out, [('C. de la Fuente Marcos', 'de la Fuente Marcos, C')])


    def test_split_long_author_list(self):
        f1 = 'tests/data/abs_files/ftp/arxiv/papers/1411/1411.4413.abs'
        meta: metadata = AbsMetaSession.parse_abs_file(filename=f1)
        alst = split_long_author_list(queries_for_authors(meta.authors), 20)
        self.assertIs(type(alst), tuple)
        self.assertIs(len(alst), 3)
        self.assertIs(type(alst[0]), list)
        self.assertIs(type(alst[1]), list)
        self.assertGreater(len(alst[1]), 0)
        self.assertIs(type(alst[2]), int)