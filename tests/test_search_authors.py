"""Tests for search service author link creation. """

from unittest import TestCase

from browse.services.search.search_authors import queries_for_authors


class TestAuthorLinkCreation(TestCase):
    def test_basic(self):
        out = queries_for_authors('Fred')
        self.assertIsInstance(out, list)
        self.assertListEqual(out, [('Fred', 'Fred')])

        out = queries_for_authors('J. R. Webb')
        self.assertIsInstance(out, list)
        self.assertListEqual(out, [('J. R. Webb', 'Webb J, R')])


        out = queries_for_authors('J. R. Webb, Fred')
        self.assertIsInstance(out, list)
        self.assertListEqual(out, [('J. R. Webb', 'Webb J, R'),', ',('Fred','Fred')])
