from unittest import TestCase

from app import app


class BibexTest(TestCase):
    def setUp(self):
        app.testing = True
        app.config["APPLICATION_ROOT"] = ""
        self.app = app.test_client()

    def test_bibex_supporting_meta_tags(self):
        """Test that meta tags get set correctly to support bibex."""
        arxiv_id = "0906.3421"

        rv = self.app.get(f"/abs?id={arxiv_id}")
        self.assertEqual(rv.status_code, 200)
        txt = rv.data.decode('utf-8')

        self.assertIn(
            f'<meta name="citation_arxiv_id" content="{arxiv_id}" />',
            txt,
            "Must have the paper id meta tag",
        )

        self.assertNotIn(
            f'<meta name="citation_doi" content="10.48550/arXiv.{arxiv_id}" />',
            txt,
            "Must not have the datacite DOI overriding the jref-DOI ARXIVCE-264",
        )

        self.assertIn(
            '<meta name="citation_doi" content="10.3842/SIGMA.2010.014" />',
            txt,
            "citation meta tag must have jref DOI",
        )
