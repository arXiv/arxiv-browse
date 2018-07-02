"""Tests for external reference and citation configuration and utilities."""
from unittest import TestCase, mock

from arxiv.taxonomy import CATEGORIES
from browse.domain.metadata import Category
from browse.domain.identifier import Identifier
from browse.services.document.config.external_refs_cits \
    import INSPIRE_REF_CIT_CATEGORIES
from browse.services.util.external_refs_cits import include_inspire_link


class TestExternalReferencesCitations(TestCase):
    """Tests for external reference and citation config and utilities."""

    def test_inspire_config(self):
        """Ensure INSPIRE_REF_CIT_CATEGORIES categories are valid."""
        for category in INSPIRE_REF_CIT_CATEGORIES:
            self.assertIn(category, CATEGORIES)

    @mock.patch('browse.domain.metadata.DocMetadata')
    def test_include_inspire_link(self, mock_docmeta):
        """Tests for the include_inspire_link function."""
        mock_docmeta.arxiv_identifier = Identifier('1201.0001')
        mock_docmeta.primary_category = Category('hep-th')
        self.assertTrue(include_inspire_link(mock_docmeta))

        mock_docmeta.arxiv_identifier = Identifier('1212.0001')
        mock_docmeta.primary_category = Category('astro-ph.CO')
        self.assertFalse(include_inspire_link(mock_docmeta))

        mock_docmeta.arxiv_identifier = Identifier('1301.0001')
        mock_docmeta.primary_category = Category('astro-ph.CO')
        self.assertTrue(include_inspire_link(mock_docmeta))

        mock_docmeta.arxiv_identifier = Identifier('1806.01234')
        mock_docmeta.primary_category = Category('physics.ins-det')
        self.assertTrue(include_inspire_link(mock_docmeta))

        mock_docmeta.arxiv_identifier = Identifier('1212.0002')
        mock_docmeta.primary_category = Category('physics.gen-ph')
        self.assertFalse(include_inspire_link(mock_docmeta))
