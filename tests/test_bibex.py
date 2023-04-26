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

    def test_good_bibtex(self):
        rv = self.app.get(f"/bibtex/0906.3421")
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get(f"/bibtex/0906.3421v1")
        self.assertEqual(rv.status_code, 200)

    def test_bibex_none(self):
        """Don't do a 500 for /bibex/None ARXIVCE-339."""
        rv = self.app.get(f"/bibtex/None")
        self.assertEqual(rv.status_code, 400)

    def test_bab_bibtex(self):
        rv = self.app.get(f"/bibtex/0906.3421v9999")
        self.assertEqual(rv.status_code, 404)

        rv = self.app.get(f"/bibtex/cs")
        self.assertEqual(rv.status_code, 400)

        rv = self.app.get(f"/bibtex/0906.3ab1")
        self.assertEqual(rv.status_code, 400)

        rv = self.app.get(f"/bibtex/0913.1234")
        self.assertEqual(rv.status_code, 400)
