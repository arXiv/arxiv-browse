"""Tests for external reference and citation configuration and utilities."""
from unittest import TestCase, mock

from browse.domain.identifier import Identifier
from browse.formating.external_refs_cits \
    import INSPIRE_REF_CIT_CATEGORIES, DBLP_ARCHIVES
from browse.formating.external_refs_cits import include_inspire_link,\
    get_dblp_bibtex_path, include_dblp_section, get_computed_dblp_listing_path

from browse.domain.category import Category
from browse.domain.metadata import Archive

from arxiv.taxonomy import CATEGORIES, ARCHIVES

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

    def test_dblp_config(self):
        """Ensure DBLP_ARCHIVES archives are valid."""
        for archive in DBLP_ARCHIVES:
            self.assertIn(archive, ARCHIVES)

    def test_get_dblp_listing_path(self):
        """Tests for DBLP bibtex path generation."""
        listing_url = 'db/journals/corr/corr0002.html#nlin-AO-0002040'
        self.assertEqual(get_dblp_bibtex_path(listing_url),
                         'journals/corr/nlin-AO-0002040')

        listing_url = 'db/conf/aadebug/aadebug2000.html#Herranz-NievaM00'
        self.assertEqual(get_dblp_bibtex_path(listing_url),
                         'conf/aadebug/Herranz-NievaM00')

        listing_url = 'db/conf/aadebug/aadebug2000.html'
        self.assertIsNone(get_dblp_bibtex_path(listing_url))

        listing_url = 'db/foo/aadebug/aadebug2000.html#Herranz-NievaM00'
        self.assertIsNone(get_dblp_bibtex_path(listing_url))

    @mock.patch('browse.domain.metadata.DocMetadata')
    def test_include_dblp_section(self, mock_docmeta):
        """Tests for the include_dblp_section fallback (from DB) function."""
        mock_docmeta.arxiv_identifier = Identifier('1806.00001')
        mock_docmeta.primary_archive = Archive('cs')
        self.assertTrue(include_dblp_section(mock_docmeta))
        self.assertEqual(get_computed_dblp_listing_path(mock_docmeta),
                         'db/journals/corr/corr1806.html#abs-1806-00001')

        mock_docmeta.arxiv_identifier = Identifier('cs/0501001')
        mock_docmeta.primary_archive = Archive('cs')
        self.assertTrue(include_dblp_section(mock_docmeta))
        self.assertEqual(get_computed_dblp_listing_path(mock_docmeta),
                         'db/journals/corr/corr0501.html#abs-cs-0501001')

        mock_docmeta.arxiv_identifier = Identifier('cs/0412001')
        mock_docmeta.primary_archive = Archive('cs')
        self.assertTrue(include_dblp_section(mock_docmeta))
        self.assertIsNone(get_computed_dblp_listing_path(mock_docmeta))

        mock_docmeta.arxiv_identifier = Identifier('1806.00002')
        mock_docmeta.primary_archive = Archive('math')
        self.assertFalse(include_dblp_section(mock_docmeta))
