"""Tests for search service author link creation. """

from unittest import TestCase

from arxiv.util.authors import split_authors

from browse.formatting.search_authors import queries_for_authors, split_long_author_list
from tests import path_of_for_test, TestLocalAbsAccessor

from arxiv.document.metadata import DocMetadata
from arxiv.identifier import Identifier
from arxiv.document.parse_abs import parse_abs_file_accessor


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
                                   ' (a)', ', ', ('Jim Smith', 'Smith, J'),
                                   ' (b)', ' (c)'])

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
        meta: DocMetadata = parse_abs_file_accessor(
            TestLocalAbsAccessor(Identifier('1411.4413'), latest=True)
        )
        alst = split_long_author_list(
            queries_for_authors(str(meta.authors)), 20)
        self.assertIs(type(alst), tuple)
        self.assertIs(len(alst), 3)
        self.assertIs(type(alst[0]), list)
        self.assertIs(type(alst[1]), list)
        self.assertGreater(len(alst[1]), 0)
        self.assertIs(type(alst[2]), int)

    def test_split_with_collaboration(self):
        meta: DocMetadata = parse_abs_file_accessor(
            TestLocalAbsAccessor(Identifier('0808.4142'), latest=True)
        )
        split = split_authors(str(meta.authors))
        self.assertListEqual(
            split, ['D0 Collaboration', ':', 'V. Abazov', ',', 'et al'])

        alst = queries_for_authors(str(meta.authors))
        self.assertListEqual(alst, [('D0 Collaboration', 'D0 Collaboration'),
                                    ': ', ('V. Abazov', 'Abazov, V'), ', ', 'et al'])

    def test_split_strange_author_list(self):
        """Test odd author list that shows '0 additional authors' ARXIVNG-2083"""
        meta: DocMetadata = parse_abs_file_accessor(
            TestLocalAbsAccessor(Identifier('1902.05884'), latest=True)
        )
        alst = split_long_author_list(
            queries_for_authors(str(meta.authors)), 100)

        self.assertIs(type(alst), tuple)
        self.assertIs(len(alst), 3)

        self.assertIs(type(alst[0]), list)
        self.assertIs(type(alst[1]), list)
        self.assertIs(type(alst[2]), int)

        self.assertEqual(
            len(list(filter(lambda x: isinstance(x, tuple), alst[0]))),
            101)

        self.assertEqual(
            len(alst[1]), 0, "Back list on 1902.05884 should be empty")
        self.assertEqual(
            alst[2], 0, "Back list size on 1902.05884 should be empty")
