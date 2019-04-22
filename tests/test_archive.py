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
        self.assertIn('Expires', rv.headers, 'Should have expires header')

        rv = self.app.get("/archive/astro-ph/")
        self.assertEqual(rv.status_code, 200,
                         'Trailing slash should be allowed')

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

    def test_subsumed_archive(self):
        rv = self.app.get("/archive/comp-lg")
        self.assertEqual(rv.status_code, 404)
        src = rv.data.decode("utf-8")

        self.assertIn("Computer Science", src)
        self.assertIn("cs.CL", src)

        rv = self.app.get("/archive/acc-phys")
        self.assertEqual(rv.status_code, 200)
        src = rv.data.decode("utf-8")

        self.assertIn("Accelerator Physics", src)
        self.assertIn("physics.acc-ph", src)

    def test_single_archive(self):
        rv = self.app.get("/archive/hep-ph")
        self.assertEqual(rv.status_code, 200)
        src = rv.data.decode("utf-8")

        self.assertIn("High Energy Physics", src)
        self.assertNotIn("Categories within", src)
