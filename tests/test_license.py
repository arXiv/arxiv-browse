from unittest import TestCase
from browse.domain.license import ASSUMED_LICENSE_URI


class TestLicense(TestCase):
    def test_new_license(self):
        from browse.domain.license import License

        r_uri = 'http://bogus/license/uri'
        lic = License(r_uri)
        self.assertNotEqual(lic, None)
        self.assertEqual(lic.recorded_uri, r_uri)
        self.assertEqual(lic.effective_license_uri, r_uri)

        lic = License(None)
        self.assertNotEqual(lic, None)
        self.assertEqual(lic.recorded_uri, None)
        self.assertEqual(lic.effective_license_uri, ASSUMED_LICENSE_URI)

        with self.assertRaises(TypeError):
            lic = License(23)
