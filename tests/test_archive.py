import unittest

from app import app


class BrowseTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        app.config["APPLICATION_ROOT"] = ""
        self.app = app.test_client()

    def test_astroph_archive(self):
        rv = self.app.get("/archive/astro-ph")
        self.assertEqual(rv.status_code, 200)
        src = rv.data.decode("utf-8")
        self.assertIn("Astrophysics", src)
        self.assertIn("/year/astro-ph/92", src)
        self.assertIn("/year/astro-ph/19", src)

        self.assertIn(
            "Astrophysics of Galaxies",
            src,
            "Subcategories of astro-ph should be on archive page",
        )
        self.assertIn(
            "Earth and Planetary Astrophysics",
            src,
            "Subcategories of astro-ph should be on archive page",
        )

    def test_list(self):
        rv = self.app.get("/archive/list")
        self.assertEqual(rv.status_code, 200)
        src = rv.data.decode("utf-8")

        self.assertIn("Astrophysics", src)
        self.assertIn("astro-ph", src)

        self.assertIn("Materials Theory", src)
        self.assertIn("mtrl-th", src)

        rv = self.app.get("/archive/bogus-archive")
        self.assertEqual(rv.status_code, 404)
